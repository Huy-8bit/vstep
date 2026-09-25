from datetime import timedelta

from sqlalchemy import select

from app.common.errors import AppError
from app.common.words import count_words
from app.db.base import utcnow
from app.models import ExamSession, WritingAttempt, WritingQuestion
from app.models.commerce import ProductEvent
from app.repositories.writing import owned_attempt, owned_exam
from app.schemas.api import AnswerUpdate, ExamCreate, ExamSubmit
from app.schemas.writing import QuestionRequest
from app.services.question_generator import QuestionGeneratorService
from app.vstep_reference.specification import OFFICIAL_FORMAT, SIMULATOR_HEURISTICS


class ExamService:
    def __init__(self, db, llm):
        self.db = db
        self.questions = QuestionGeneratorService(db, llm)

    async def create(self, data: ExamCreate, user_id: str, *, library=None, trial_only=False, access_source="VIP"):
        tasks = [1, 2] if data.mode == "FULL_TEST" else [1 if data.mode == "TASK1" else 2]
        questions = []
        if data.question_ids:
            questions = list(
                await self.db.scalars(
                    select(WritingQuestion).where(WritingQuestion.id.in_(data.question_ids))
                )
            )
            if sorted(q.task_type for q in questions) != tasks or any(
                q.owner_id not in (None, user_id)
                or (q.owner_id is None and (not q.generation_diagnostics.get("quality_valid") or not q.is_published or q.access_tier == "INTERNAL"))
                or (trial_only and (q.owner_id is not None or not q.available_for_free_trial or q.access_tier != "FREE_TRIAL"))
                for q in questions
            ):
                raise AppError(422, "Đề đã chọn không phù hợp với chế độ luyện tập.")
        else:
            for task in tasks:
                questions.append(
                    await self.questions.generate(
                        QuestionRequest(task=task, test_profile=data.test_profile), user_id, trial_only=trial_only
                    )
                )
        now = utcnow()
        if data.mode == "FULL_TEST" and any(q.generation_diagnostics.get("learning_focus") for q in questions):
            raise AppError(422, "Đề luyện điểm yếu không được dùng trong bài thi đầy đủ.")
        minutes = (
            OFFICIAL_FORMAT["writing"]["minutes"]
            if data.mode == "FULL_TEST"
            else SIMULATOR_HEURISTICS["writing_task_minutes"][tasks[0]]
        )
        if library is None and questions and questions[0].library_question_id:
            library = {"library_question_id": questions[0].library_question_id, "library_revision": questions[0].library_revision, "library_title": questions[0].library_title}
        exam = ExamSession(
            **(library or {}),
            user_id=user_id,
            mode=data.mode,
            access_source=access_source,
            test_profile=data.test_profile,
            started_at=now,
            expires_at=now + timedelta(minutes=minutes) if data.timed or data.mode == "FULL_TEST" else None,
        )
        exam.attempts = [
            WritingAttempt(
                user_id=user_id,
                question_id=q.id,
                question=q,
                task_type=q.task_type,
                started_at=now,
                answer="",
                word_count=0,
                revision=0,
                status="DRAFT",
            )
            for q in sorted(questions, key=lambda q: q.task_type)
        ]
        self.db.add(exam)
        await self.db.commit()
        return await owned_exam(self.db, exam.id, user_id)

    async def finalize(self, exam: ExamSession, expired: bool = False):
        if exam.status != "IN_PROGRESS":
            return
        now = exam.expires_at if expired else utcnow()
        exam.status = "EXPIRED" if expired else "SUBMITTED"
        exam.submitted_at = now
        for attempt in exam.attempts:
            attempt.status = "SUBMITTED"
            attempt.submitted_at = now
            attempt.duration_seconds = max(0, int((now - attempt.started_at).total_seconds()))
        if not expired:
            self.db.add(ProductEvent(user_id=exam.user_id, name="PRACTICE_COMPLETED", details={"skill": "WRITING", "session_id": exam.id, "access_source": exam.access_source}))
        await self.db.commit()

    async def get(self, exam_id: str, user_id: str):
        exam = await owned_exam(self.db, exam_id, user_id, lock=True)
        if exam.status == "IN_PROGRESS" and exam.expires_at and utcnow() >= exam.expires_at:
            await self.finalize(exam, expired=True)
        return exam

    @staticmethod
    def update_answer(attempt: WritingAttempt, data: AnswerUpdate):
        if data.revision != attempt.revision:
            # Safe idempotent retry when the acknowledgement was lost.
            if data.answer == attempt.answer:
                return
            raise AppError(
                409,
                "Bài đã thay đổi ở tab khác. Bản nháp trên thiết bị vẫn được giữ; hãy tải lại để đồng bộ.",
                "revision_conflict",
            )
        attempt.answer = data.answer
        attempt.word_count = count_words(data.answer)
        attempt.revision += 1

    async def save(self, attempt_id: str, user_id: str, data: AnswerUpdate):
        attempt = await owned_attempt(self.db, attempt_id, user_id)
        exam = await self.get(attempt.exam_session_id, user_id)
        if exam.status != "IN_PROGRESS":
            raise AppError(409, "Bài đã nộp hoặc đã hết giờ. Không thể sửa bài.", "exam_closed")
        attempt = next(a for a in exam.attempts if a.id == attempt_id)
        self.update_answer(attempt, data)
        await self.db.commit()
        return attempt

    async def submit(self, exam_id: str, user_id: str, data: ExamSubmit):
        exam = await self.get(exam_id, user_id)
        if exam.status != "IN_PROGRESS":
            return exam
        if not set(data.answers).issubset({a.id for a in exam.attempts}):
            raise AppError(422, "Bài làm không thuộc phiên thi này.")
        for attempt in exam.attempts:
            if attempt.id in data.answers:
                self.update_answer(attempt, data.answers[attempt.id])
        await self.finalize(exam)
        return exam
