from datetime import timedelta

from sqlalchemy import select

from app.common.errors import AppError
from app.db.base import utcnow
from app.learning.signals import sync_learning
from app.models.reading import ReadingAnswer, ReadingExamSession, ReadingPassage
from app.services.reading_blueprint import READING_BLUEPRINT
from app.services.reading_question_generator import ReadingQuestionGeneratorService
from app.services.reading_scoring_service import ReadingScoringService
from app.vstep_reference.specification import OFFICIAL_FORMAT


async def owned_reading_session(db, session_id, user_id, lock=False):
    query = select(ReadingExamSession).where(
        ReadingExamSession.id == session_id, ReadingExamSession.user_id == user_id
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    session = await db.scalar(query)
    if not session:
        raise AppError(404, "Không tìm thấy phiên Reading.")
    return session


class ReadingExamService:
    def __init__(self, db, llm=None):
        self.db, self.llm = db, llm

    async def create(self, data, user_id, *, selection=None, library=None):
        selected = selection if selection is not None else await ReadingQuestionGeneratorService(self.db, self.llm).select(data, user_id)
        if any(p.owner_id not in (None, user_id) for p, _ in selected):
            raise AppError(404, "Không tìm thấy bài đọc.")
        now = utcnow()
        selected_topics = {p.topic for p, _ in selected}
        minutes = (
            OFFICIAL_FORMAT["reading"]["minutes"]
            if data.mode == "FULL_TEST"
            else 15
            if data.mode == "PASSAGE_PRACTICE"
            else 8
        )
        session = ReadingExamSession(
            **(library or {}),
            user_id=user_id,
            mode=data.mode,
            test_profile=data.test_profile,
            blueprint_version=READING_BLUEPRINT.version if data.mode == "FULL_TEST" and not library else None,
            blueprint_diagnostics=READING_BLUEPRINT.diagnostics(list({p.id: p for p, _ in selected}.values()))
            if data.mode == "FULL_TEST" and not library
            else {},
            topic=next(iter(selected_topics)) if len(selected_topics) == 1 else "random",
            started_at=now,
            expires_at=now + timedelta(minutes=minutes) if data.mode == "FULL_TEST" or data.timed else None,
            question_count=len(selected),
            passage_ids=list(dict.fromkeys(p.id for p, _ in selected)),
            question_ids=[q.id for _, q in selected],
            result=None,
        )
        session.answers = [
            ReadingAnswer(
                question_id=q.id,
                question=q,
                selected_answer=None,
                is_marked_for_review=False,
                revision=0,
                time_spent_seconds=0,
            )
            for _, q in selected
        ]
        self.db.add(session)
        await self.db.commit()
        return session

    async def get(self, session_id, user_id):
        session = await owned_reading_session(self.db, session_id, user_id, lock=True)
        if session.status == "IN_PROGRESS" and session.expires_at and utcnow() >= session.expires_at:
            ReadingScoringService().finalize(session, expired=True)
            await self.db.commit()
            await sync_learning(user_id, "READING", session_id)
        return session

    def apply(self, session, changes):
        answers = {a.question_id: a for a in session.answers}
        if not set(changes).issubset(answers):
            raise AppError(422, "Có câu hỏi không thuộc phiên Reading này.")
        # Validate the entire batch before mutating any row.
        for question_id, change in changes.items():
            answer = answers[question_id]
            same = (
                answer.selected_answer == change.selected_answer
                and answer.is_marked_for_review == change.is_marked_for_review
            )
            if answer.revision != change.revision and not same:
                raise AppError(
                    409,
                    "Đáp án đã thay đổi ở tab khác. Hãy chọn bản trên thiết bị hoặc trên máy chủ để tiếp tục.",
                    "revision_conflict",
                )
        now = utcnow()
        elapsed = max(0, int((now - session.started_at).total_seconds()))
        for question_id, change in changes.items():
            answer = answers[question_id]
            answer.time_spent_seconds = max(
                answer.time_spent_seconds, min(change.time_spent_seconds, elapsed)
            )
            if not answer.first_viewed_at and (change.time_spent_seconds or change.selected_answer):
                answer.first_viewed_at = now
            if answer.revision != change.revision:
                continue  # Acknowledgement lost; identical retry does not overwrite newer time data.
            if answer.selected_answer != change.selected_answer:
                answer.answered_at = now if change.selected_answer else None
            answer.selected_answer = change.selected_answer
            answer.is_marked_for_review = change.is_marked_for_review
            answer.revision += 1

    async def save(self, session_id, user_id, changes):
        session = await self.get(session_id, user_id)
        if session.status != "IN_PROGRESS":
            return session  # Expiry has already finalized the authoritative saved answers.
        self.apply(session, changes)
        await self.db.commit()
        return session

    async def submit(self, session_id, user_id, changes):
        session = await self.get(session_id, user_id)
        if session.status != "IN_PROGRESS":
            return session
        self.apply(session, changes)
        ReadingScoringService().finalize(session)
        await self.db.commit()
        await sync_learning(user_id, "READING", session_id)
        return session

    async def expire_pending(self, user_id):
        sessions = await self.db.scalars(
            select(ReadingExamSession)
            .where(
                ReadingExamSession.user_id == user_id,
                ReadingExamSession.status == "IN_PROGRESS",
                ReadingExamSession.expires_at <= utcnow(),
            )
            .with_for_update()
        )
        finalized = list(sessions)
        for session in finalized:
            ReadingScoringService().finalize(session, expired=True)
        await self.db.commit()
        for session in finalized:
            await sync_learning(user_id, "READING", session.id)

    async def passages(self, session):
        rows = await self.db.scalars(select(ReadingPassage).where(ReadingPassage.id.in_(session.passage_ids)))
        by_id = {p.id: p for p in rows}
        return [by_id[pid] for pid in session.passage_ids]
