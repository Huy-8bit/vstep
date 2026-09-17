from datetime import timedelta

from sqlalchemy import select

from app.common.errors import AppError
from app.common.words import count_words
from app.db.base import utcnow
from app.models import ExamSession, WritingAttempt, WritingQuestion
from app.repositories.writing import owned_attempt, owned_exam
from app.schemas.api import AnswerUpdate, ExamCreate, ExamSubmit
from app.schemas.writing import QuestionRequest
from app.services.question_generator import QuestionGeneratorService


class ExamService:
    def __init__(self, db, llm):
        self.db = db
        self.questions = QuestionGeneratorService(db, llm)

    async def create(self, data: ExamCreate, user_id: str):
        tasks = [1, 2] if data.mode == "FULL_TEST" else [1 if data.mode == "TASK1" else 2]
        questions = []
        if data.question_ids:
            questions = list(
                await self.db.scalars(
                    select(WritingQuestion).where(WritingQuestion.id.in_(data.question_ids))
                )
            )
            if sorted(q.task_type for q in questions) != tasks:
                raise AppError(422, "Đề đã chọn không phù hợp với chế độ luyện tập.")
        else:
            for task in tasks:
                questions.append(await self.questions.generate(QuestionRequest(task=task), user_id))
        now = utcnow()
        minutes = 60 if data.mode == "FULL_TEST" else (20 if tasks[0] == 1 else 40)
        exam = ExamSession(
            user_id=user_id,
            mode=data.mode,
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
