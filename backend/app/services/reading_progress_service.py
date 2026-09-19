from collections import defaultdict
from statistics import mean

from sqlalchemy import func, select

from app.api.library_metadata import library_metadata
from app.models.reading import ReadingExamSession, ReadingPassage
from app.services.reading_exam_service import ReadingExamService
from app.services.reading_scoring_service import breakdown, trusted_key


class ReadingProgressService:
    def __init__(self, db):
        self.db = db

    async def history(self, user_id, mode, offset, limit):
        await ReadingExamService(self.db).expire_pending(user_id)
        query = select(ReadingExamSession).where(ReadingExamSession.user_id == user_id)
        if mode:
            query = query.where(ReadingExamSession.mode == mode)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        sessions = await self.db.scalars(
            query.order_by(ReadingExamSession.created_at.desc()).offset(offset).limit(limit)
        )
        return {
            "total": total,
            "items": [
                {
                    **library_metadata(s),
                    "id": s.id,
                    "mode": s.mode,
                    "test_profile": s.test_profile,
                    "topic": s.topic,
                    "status": s.status,
                    "started_at": s.started_at,
                    "question_count": s.question_count,
                    "correct_count": s.result.correct_count if s.result else None,
                    "accuracy": s.result.accuracy if s.result else None,
                    "score": s.result.score if s.result else None,
                    "duration_seconds": s.result.duration_seconds if s.result else None,
                }
                for s in sessions
            ],
        }

    async def progress(self, user_id, mode=None):
        await ReadingExamService(self.db).expire_pending(user_id)
        query = select(ReadingExamSession).where(
            ReadingExamSession.user_id == user_id, ReadingExamSession.status != "IN_PROGRESS"
        )
        if mode:
            query = query.where(ReadingExamSession.mode == mode)
        sessions = list(await self.db.scalars(query.order_by(ReadingExamSession.submitted_at)))
        sessions = [s for s in sessions if s.result]
        passage_ids = {pid for s in sessions for pid in s.passage_ids}
        passages = {
            p.id: p
            for p in await self.db.scalars(select(ReadingPassage).where(ReadingPassage.id.in_(passage_ids)))
        }
        by_type, by_topic = defaultdict(list), defaultdict(list)
        for s in sessions:
            for a in s.answers:
                by_type[a.question.question_type].append(a)
                by_topic[passages[a.question.passage_id].topic].append(a)
        total = sum(s.question_count for s in sessions)
        correct = sum(s.result.correct_count for s in sessions)
        answered = sum(a.selected_answer is not None for s in sessions for a in s.answers)
        scorable = sum(trusted_key(a.question) for s in sessions for a in s.answers)
        scores = [s.result.score for s in sessions if s.result.score is not None]
        types = breakdown(by_type)
        weaknesses = sorted(
            [row for row in types if row["accuracy"] is not None and row["accuracy"] < 100], key=lambda row: (row["accuracy"], -row["total"])
        )[:3]
        return {
            "completed_sessions": len(sessions),
            "questions_total": total,
            "questions_answered": answered,
            "correct_count": correct,
            "accuracy": round(correct / scorable * 100, 1) if scorable else None,
            "scorable_count": scorable,
            "unscored_count": total - scorable,
            "average_score": round(mean(scores), 2) if scores else None,
            "average_time_per_question": round(sum(s.result.duration_seconds for s in sessions) / total, 1)
            if total
            else None,
            "question_types": types,
            "topics": breakdown(by_topic),
            "weaknesses": weaknesses,
            "timeline": [
                {
                    **library_metadata(s),
                    "id": s.id,
                    "date": s.submitted_at,
                    "mode": s.mode,
                    "score": s.result.score,
                    "accuracy": s.result.accuracy,
                }
                for s in sessions
            ],
        }
