import random

from sqlalchemy import select

from app.common.errors import AppError
from app.db.base import utcnow
from app.models.commerce import ProductEvent
from app.models.speaking import SpeakingAnswer, SpeakingExamSession, SpeakingQuestion
from app.schemas.speaking import SpeakingQuestionRequest, SpeakingSessionCreate
from app.services.speaking_question_generator import SpeakingQuestionGeneratorService


async def owned_speaking_session(db, session_id: str, user_id: str, lock: bool = False):
    query = select(SpeakingExamSession).where(
        SpeakingExamSession.id == session_id, SpeakingExamSession.user_id == user_id
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    session = await db.scalar(query)
    if not session:
        raise AppError(404, "Không tìm thấy phiên Speaking.")
    return session


async def owned_speaking_answer(db, answer_id: str, user_id: str):
    answer = await db.scalar(
        select(SpeakingAnswer)
        .join(SpeakingExamSession)
        .where(SpeakingAnswer.id == answer_id, SpeakingExamSession.user_id == user_id)
    )
    if not answer:
        raise AppError(404, "Không tìm thấy câu trả lời.")
    return answer


def question_steps(q: SpeakingQuestion) -> list[dict]:
    base = {
        "question_id": q.id,
        "part": q.part,
        "topic_code": q.topic,
        "topic": (q.presentation or {}).get("topic_title") or q.topic,
        "options": [],
        "suggested_ideas": [],
        "situation": None,
        "allow_own_idea": False,
        "practice_asset_ids": (q.presentation or {}).get("practice_asset_ids", []),
        "optional_context": (q.presentation or {}).get("optional_context", ""),
    }
    if q.part == 1:
        return [
            {**base, "kind": "interaction", "topic": topic["topic"], "question_text": text}
            for topic in q.topic_sets
            for text in topic["questions"]
        ]
    if q.part == 2:
        return [
            {
                **base,
                "kind": "solution",
                "question_text": q.question_text,
                "situation": q.situation,
                "options": q.options,
            }
        ]
    return [
        {
            **base,
            "kind": "main_talk",
            "question_text": q.question_text,
            "suggested_ideas": q.suggested_ideas,
            "allow_own_idea": True,
        },
        *[{**base, "kind": "follow_up", "question_text": text} for text in q.follow_up_questions],
    ]


class SpeakingExamService:
    def __init__(self, db, llm, storage):
        self.db, self.llm, self.storage = db, llm, storage

    async def create(self, data: SpeakingSessionCreate, user_id: str, *, resolved_questions=None, library=None, trial_only=False, access_source="VIP"):
        parts = (
            [1, 2, 3]
            if data.mode == "FULL_TEST"
            else [{"PART1": 1, "PART2": 2, "PART3": 3, "QUICK_PRACTICE": 1}[data.mode]]
        )
        if data.question_id and data.mode == "FULL_TEST":
            raise AppError(422, "Đề thi Speaking đầy đủ được hệ thống chọn cho cả ba phần.")
        steps = []
        for part in parts:
            if resolved_questions is not None:
                q = next((q for q in resolved_questions if q.part == part and q.owner_id == user_id), None)
                if q is None:
                    raise AppError(422, "Thiếu phần Speaking trong đề riêng.")
            elif data.question_id:
                q = await self.db.get(SpeakingQuestion, data.question_id)
                if not q or q.part != part or q.owner_id not in (None, user_id) or (q.owner_id is None and (not q.generation_diagnostics.get("quality_valid") or not q.is_published or q.access_tier == "INTERNAL")) or (trial_only and (q.owner_id is not None or not q.available_for_free_trial or q.access_tier != "FREE_TRIAL")):
                    raise AppError(422, "Đề không khớp phần Speaking đã chọn.")
            else:
                q = await SpeakingQuestionGeneratorService(self.db, self.llm).generate(
                    SpeakingQuestionRequest(
                        part=part, topic=data.topic, source=data.source, test_profile=data.test_profile
                    ),
                    user_id, trial_only=trial_only,
                )
            steps.extend(question_steps(q))
        if data.mode == "QUICK_PRACTICE":
            steps = [random.choice(steps)]
        for index, step in enumerate(steps):
            step["sequence_number"] = index
        if library is None and q.library_question_id:
            library = {"library_question_id": q.library_question_id, "library_revision": q.library_revision, "library_title": q.library_title}
        session = SpeakingExamSession(
            **(library or {}),
            user_id=user_id,
            mode=data.mode,
            access_source=access_source,
            test_profile=data.test_profile,
            current_part=steps[0]["part"],
            current_sequence=0,
            question_set=steps,
            answers=[],
            grading=None,
        )
        self.db.add(session)
        await self.db.commit()
        return session

    async def start_answer(self, session_id: str, user_id: str, sequence: int):
        session = await owned_speaking_session(self.db, session_id, user_id, lock=True)
        if (
            session.status != "IN_PROGRESS"
            or session.current_sequence != sequence
            or sequence >= len(session.question_set)
        ):
            raise AppError(409, "Câu hỏi này chưa được mở hoặc phiên đã kết thúc.", "speaking_step_closed")
        existing = next((a for a in session.answers if a.sequence_number == sequence), None)
        if existing:
            return existing
        step = session.question_set[sequence]
        answer = SpeakingAnswer(
            session_id=session.id,
            question_id=step["question_id"],
            part=step["part"],
            question_text=step["question_text"],
            sequence_number=sequence,
            status="RECORDING",
            metrics={},
            grading=None,
        )
        self.db.add(answer)
        await self.db.commit()
        return answer

    async def upload(self, answer_id: str, user_id: str, file):
        answer = await owned_speaking_answer(self.db, answer_id, user_id)
        session = await owned_speaking_session(self.db, answer.session_id, user_id)
        if session.status != "IN_PROGRESS":
            raise AppError(409, "Phiên đã kết thúc; bản ghi không thể thay đổi.", "speaking_closed")
        # Decode outside the session lock, then recheck state before attaching the immutable asset.
        stored = await self.storage.store(file, user_id)
        session = await owned_speaking_session(self.db, session.id, user_id, lock=True)
        await self.db.refresh(answer)
        if answer.audio_hash == stored.sha256:
            self.storage.remove(stored.path)
            return answer  # Retrying a lost upload acknowledgement is safe.
        if (
            session.status != "IN_PROGRESS"
            or session.current_sequence != answer.sequence_number
            or answer.status == "SKIPPED"
        ):
            self.storage.remove(stored.path)
            raise AppError(409, "Câu trả lời đã được chốt.", "speaking_step_closed")
        if session.mode == "FULL_TEST" and answer.audio_path:
            self.storage.remove(stored.path)
            raise AppError(409, "Thi thử chỉ nhận một bản ghi cho mỗi câu.", "exam_no_retake")
        previous_path = answer.audio_path
        answer.audio_path = answer.normalized_audio_path = stored.path
        answer.audio_hash, answer.audio_duration_ms = stored.sha256, stored.duration_ms
        answer.mime_type, answer.audio_size, answer.metrics = stored.mime_type, stored.size, stored.metrics
        answer.transcript = answer.transcript_hash = answer.transcription_key = answer.transcription_model = (
            None
        )
        answer.audio_analysis = answer.audio_analysis_key = None
        answer.word_count = 0
        answer.status, answer.submitted_at = "UPLOADED", utcnow()
        # Practice feedback is invalidated when a new take is explicitly uploaded.
        if answer.grading:
            await self.db.delete(answer.grading)
            answer.grading = None
        await self.db.commit()
        if previous_path and previous_path != stored.path:
            self.storage.remove(previous_path)
            from app.learning.signals import sync_learning

            await sync_learning(user_id, "SPEAKING", session.id)
        return answer

    async def advance(self, session_id: str, user_id: str, sequence: int, skip: bool):
        session = await owned_speaking_session(self.db, session_id, user_id, lock=True)
        if sequence < session.current_sequence:
            return session  # Idempotent Next after an acknowledgement is lost.
        if (
            session.status != "IN_PROGRESS"
            or sequence != session.current_sequence
            or sequence >= len(session.question_set)
        ):
            raise AppError(409, "Thứ tự câu trả lời không hợp lệ.", "speaking_step_closed")
        answer = next((a for a in session.answers if a.sequence_number == sequence), None)
        if not answer or not answer.audio_path:
            if not skip:
                raise AppError(
                    409, "Hãy ghi âm và tải bản ghi trước khi sang câu tiếp theo.", "audio_required"
                )
            if not answer:
                step = session.question_set[sequence]
                answer = SpeakingAnswer(
                    session_id=session.id,
                    question_id=step["question_id"],
                    part=step["part"],
                    question_text=step["question_text"],
                    sequence_number=sequence,
                    grading=None,
                )
                self.db.add(answer)
            answer.status, answer.submitted_at, answer.transcript = "SKIPPED", utcnow(), ""
        session.current_sequence += 1
        if session.current_sequence < len(session.question_set):
            session.current_part = session.question_set[session.current_sequence]["part"]
        await self.db.commit()
        return await owned_speaking_session(self.db, session_id, user_id, lock=True)

    async def complete(self, session_id: str, user_id: str):
        session = await owned_speaking_session(self.db, session_id, user_id, lock=True)
        if session.status != "IN_PROGRESS":
            return session
        if session.current_sequence != len(session.question_set):
            raise AppError(
                409, "Hãy hoàn thành các câu hỏi và follow-up trước khi nộp bài.", "speaking_incomplete"
            )
        session.status, session.completed_at = "COMPLETED", utcnow()
        self.db.add(ProductEvent(user_id=user_id, name="PRACTICE_COMPLETED", details={"skill": "SPEAKING", "session_id": session.id, "access_source": session.access_source}))
        await self.db.commit()
        return session

    async def can_review(self, answer, user_id):
        session = await owned_speaking_session(self.db, answer.session_id, user_id)
        if session.mode == "FULL_TEST" and session.status == "IN_PROGRESS":
            raise AppError(
                409, "Bản ghi và phản hồi được mở sau khi hoàn thành bài thi.", "exam_feedback_locked"
            )
        return session
