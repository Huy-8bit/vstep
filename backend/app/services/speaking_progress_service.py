from collections import Counter
from statistics import mean

from sqlalchemy import func, select

from app.api.library_metadata import library_metadata
from app.models.speaking import SpeakingExamSession, SpeakingGrading
from app.services.speaking_grading_service import SCORE_FIELDS


class SpeakingProgressService:
    def __init__(self, db):
        self.db = db

    async def history(self, user_id, mode, offset, limit):
        query = select(SpeakingExamSession).where(SpeakingExamSession.user_id == user_id)
        if mode:
            query = query.where(SpeakingExamSession.mode == mode)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        sessions = await self.db.scalars(
            query.order_by(SpeakingExamSession.created_at.desc()).offset(offset).limit(limit)
        )
        return {
            "total": total,
            "items": [
                {
                    **library_metadata(s),
                    "id": s.id,
                    "mode": s.mode,
                    "status": s.status,
                    "started_at": s.started_at,
                    "parts": sorted({q["part"] for q in s.question_set}),
                    "topics": list(dict.fromkeys(q["topic"] for q in s.question_set)),
                    "duration_seconds": round(sum(a.audio_duration_ms or 0 for a in s.answers) / 1000),
                    "score": s.grading.overall_score if s.grading else None,
                    "level": s.grading.estimated_level if s.grading else None,
                }
                for s in sessions
            ],
        }

    async def progress(self, user_id, mode=None):
        query = (
            select(SpeakingGrading, SpeakingExamSession.mode)
            .join(SpeakingExamSession, SpeakingExamSession.id == SpeakingGrading.session_id)
            .where(SpeakingGrading.user_id == user_id)
        )
        if mode:
            query = query.where(SpeakingExamSession.mode == mode)
        rows = (await self.db.execute(query.order_by(SpeakingGrading.created_at))).all()
        scores = {
            key: [getattr(g, f"{key}_score") for g, _ in rows if getattr(g, f"{key}_score") is not None]
            for key in SCORE_FIELDS
        }
        full_scores = [g.overall_score for g, m in rows if m == "FULL_TEST" and g.overall_score is not None]
        weaknesses = Counter((e.category, e.subtype) for g, _ in rows for e in g.errors)
        return {
            "graded_sessions": len(rows),
            "complete_scores": len(scores["overall"]),
            "average": {key: round(mean(values), 2) if values else None for key, values in scores.items()},
            "criterion_counts": {key: len(values) for key, values in scores.items()},
            "full_test_average": round(mean(full_scores), 2) if full_scores else None,
            "timeline": [
                {
                    "id": g.session_id,
                    "date": g.created_at,
                    "mode": m,
                    **{key: getattr(g, f"{key}_score") for key in SCORE_FIELDS},
                }
                for g, m in rows
            ],
            "weaknesses": [
                {"category": cat, "subtype": sub, "count": count}
                for (cat, sub), count in weaknesses.most_common(8)
            ],
        }
