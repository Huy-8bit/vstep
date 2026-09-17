from collections import defaultdict

from sqlalchemy import func, select

from app.models import ExamSession, WritingAttempt, WritingError, WritingGrading


class ProgressService:
    def __init__(self, db):
        self.db = db

    async def summary(self, user_id: str):
        rows = (
            await self.db.execute(
                select(
                    WritingGrading,
                    WritingAttempt.exam_session_id,
                    WritingAttempt.task_type,
                    ExamSession.mode,
                )
                .join(WritingAttempt, WritingGrading.attempt_id == WritingAttempt.id)
                .join(ExamSession, WritingAttempt.exam_session_id == ExamSession.id)
                .where(WritingAttempt.user_id == user_id)
                .order_by(WritingGrading.created_at)
            )
        ).all()
        criteria = ("task_fulfillment", "organization", "vocabulary", "grammar")
        averages = {
            key: round(sum(getattr(g, f"{key}_score") for g, *_ in rows) / len(rows), 2) if rows else None
            for key in criteria
        }
        sessions = defaultdict(dict)
        progression = []
        for g, session_id, task, mode in rows:
            sessions[session_id][task] = g.overall_score
            if mode == "FULL_TEST":
                if len(sessions[session_id]) == 2:
                    scores = sessions[session_id]
                    progression.append(
                        {
                            "date": g.created_at.isoformat(),
                            "score": (scores[1] + 2 * scores[2]) / 3,
                            "mode": mode,
                            "attempt_id": g.attempt_id,
                        }
                    )
            else:
                progression.append(
                    {
                        "date": g.created_at.isoformat(),
                        "score": g.overall_score,
                        "mode": mode,
                        "attempt_id": g.attempt_id,
                    }
                )
        full_scores = [p["score"] for p in progression if p["mode"] == "FULL_TEST"]
        return {
            "graded_attempts": len(rows),
            "completed_full_tests": len(full_scores),
            "average_writing_score": round(sum(full_scores) / len(full_scores), 2) if full_scores else None,
            "average_task_score": round(sum(g.overall_score for g, *_ in rows) / len(rows), 2)
            if rows
            else None,
            "criteria": averages,
            "progression": progression[-60:],
            "total_words": await self.db.scalar(
                select(func.coalesce(func.sum(WritingAttempt.word_count), 0)).where(
                    WritingAttempt.user_id == user_id, WritingAttempt.status != "DRAFT"
                )
            ),
        }

    async def errors(self, user_id: str):
        rows = (
            await self.db.execute(
                select(
                    WritingError.category,
                    WritingError.subtype,
                    func.count().label("count"),
                )
                .join(WritingGrading, WritingError.grading_id == WritingGrading.id)
                .join(WritingAttempt, WritingGrading.attempt_id == WritingAttempt.id)
                .where(WritingAttempt.user_id == user_id)
                .group_by(WritingError.category, WritingError.subtype)
                .order_by(func.count().desc())
                .limit(30)
            )
        ).all()
        return [{"category": c, "subtype": s, "count": n} for c, s, n in rows]
