from collections import Counter, defaultdict
from datetime import timedelta
from statistics import mean

from sqlalchemy import func, select

from app.common.errors import AppError
from app.db.base import utcnow
from app.learning import ANALYSIS_VERSION
from app.learning.aggregation import trend_from_rates
from app.learning.taxonomy import label
from app.models.learning import (
    LearningAttempt,
    LearningExerciseAnswer,
    LearningLesson,
    LearningSignal,
    UserLearningEvent,
    UserLearningProfile,
    UserWeakness,
)
from app.models.vocabulary import UserVocabularyItem


def weakness_view(w):
    return {
        k: getattr(w, k)
        for k in (
            "id",
            "skill",
            "category",
            "subcategory",
            "concept_key",
            "display_name_vi",
            "display_name_en",
            "occurrence_count",
            "affected_attempt_count",
            "recent_occurrence_count",
            "severity",
            "status",
            "mastery_status",
            "trend",
            "priority_score",
            "first_seen_at",
            "last_seen_at",
            "last_practiced_at",
            "last_success_at",
            "stats",
        )
    }


async def owned_weakness(db, identifier, user_id):
    row = await db.scalar(
        select(UserWeakness).where(UserWeakness.id == identifier, UserWeakness.user_id == user_id)
    )
    if not row:
        raise AppError(404, "Không tìm thấy nội dung học.")
    return row


class PersonalizedLearningAnalysisService:
    def __init__(self, db):
        self.db = db

    async def weaknesses(self, user_id, skill=None, category=None, status=None, limit=100, offset=0):
        query = select(UserWeakness).where(UserWeakness.user_id == user_id, UserWeakness.occurrence_count > 0)
        if skill:
            if skill in {"WRITING", "SPEAKING"}:
                query = query.where(
                    (UserWeakness.skill == skill)
                    | ((UserWeakness.skill == "CROSS") & UserWeakness.stats["skills"].contains([skill]))
                )
            else:
                query = query.where(UserWeakness.skill == skill)
        if category:
            query = query.where(UserWeakness.category == category)
        if status:
            query = query.where(UserWeakness.status == status)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.db.scalars(
            query.order_by(UserWeakness.priority_score.desc(), UserWeakness.id).offset(offset).limit(limit)
        )
        return {"total": total, "items": [weakness_view(w) for w in rows]}

    async def detail(self, identifier, user_id):
        w = await owned_weakness(self.db, identifier, user_id)
        query = select(LearningSignal).where(
            LearningSignal.user_id == user_id,
            LearningSignal.concept_key == w.concept_key,
            LearningSignal.active.is_(True),
        )
        if w.skill != "CROSS":
            query = query.where(LearningSignal.skill == w.skill)
        rows = list(
            await self.db.scalars(
                query.order_by(LearningSignal.created_at.desc(), LearningSignal.id).limit(30)
            )
        )
        lesson = await self.db.scalar(
            select(LearningLesson)
            .where(LearningLesson.user_id == user_id, LearningLesson.weakness_id == identifier)
            .order_by(LearningLesson.created_at.desc())
            .limit(1)
        )
        return {
            **weakness_view(w),
            "evidence": [self.signal_view(s) for s in rows],
            "lesson": {"id": lesson.id, "content": lesson.content, "created_at": lesson.created_at}
            if lesson
            else None,
            "mastery_requirements_vi": "Cần nhiều lượt luyện ở ít nhất 2 ngày, độ chính xác cao và dùng đúng trong nhiều bài mới. Mở bài học hoặc vắng lỗi trong một bài chưa chứng minh đã thành thạo.",
        }

    @staticmethod
    def signal_view(s):
        return {
            "id": s.id,
            "skill": s.skill,
            "attempt_id": s.attempt_id,
            "concept_key": s.concept_key,
            "original_text": s.original_text,
            "corrected_text": s.corrected_text,
            "outcome": s.outcome,
            "details": s.details,
            "created_at": s.created_at,
            "grader_version": s.grader_version,
            "analysis_version": s.analysis_version,
            "taxonomy_version": s.taxonomy_version,
        }

    async def attempt(self, user_id, skill, attempt_id):
        from app.learning.signals import SOURCE_MODELS

        model = SOURCE_MODELS[skill]
        source = await self.db.scalar(select(model).where(model.id == attempt_id, model.user_id == user_id))
        if not source:
            raise AppError(404, "Không tìm thấy bài làm.")
        if source.status in {"DRAFT", "IN_PROGRESS"}:
            return {"items": []}
        rows = list(
            await self.db.scalars(
                select(LearningSignal).where(
                    LearningSignal.user_id == user_id,
                    LearningSignal.skill == skill,
                    LearningSignal.attempt_id == attempt_id,
                    LearningSignal.active.is_(True),
                )
            )
        )
        weaknesses = {
            w.concept_key: w
            for w in await self.db.scalars(
                select(UserWeakness).where(
                    UserWeakness.user_id == user_id,
                    UserWeakness.concept_key.in_({s.concept_key for s in rows}),
                )
            )
        }
        grouped = Counter(s.concept_key for s in rows if s.outcome == "ERROR")
        return {
            "items": [
                {
                    "concept_key": k,
                    "label": label(k),
                    "count": n,
                    "weakness_id": weaknesses[k].id if k in weaknesses else None,
                }
                for k, n in grouped.most_common(8)
            ]
        }

    async def skill(self, user_id, skill):
        attempts = list(
            await self.db.scalars(
                select(LearningAttempt)
                .where(LearningAttempt.user_id == user_id, LearningAttempt.skill == skill)
                .order_by(LearningAttempt.occurred_at.desc())
                .limit(10)
            )
        )
        keys = {k for a in attempts for k in a.scores if k != "overall"}
        criteria = []
        for key in sorted(keys):
            recent = [a.scores[key] for a in attempts[:5] if a.scores.get(key) is not None]
            older = [a.scores[key] for a in attempts[5:10] if a.scores.get(key) is not None]
            criteria.append(
                {
                    "criterion": key,
                    "recent_average": round(mean(recent), 2) if recent else None,
                    "older_average": round(mean(older), 2) if older else None,
                    "samples": len(recent),
                    "trend": trend_from_rates(
                        mean(older) if len(older) >= 3 else None,
                        mean(recent) if len(recent) >= 3 else None,
                        higher_is_better=True,
                    ),
                }
            )
        result = {
            "skill": skill,
            "criteria": criteria,
            "weaknesses": (await self.weaknesses(user_id, skill=skill))["items"],
        }
        if skill == "READING":
            result["question_types"] = await self.reading_types(user_id)
        if skill == "SPEAKING":
            result["audio_note_vi"] = (
                "Phát âm và độ trôi chảy chỉ tính khi có audio đủ tin cậy; thiếu audio không tương đương điểm 0."
            )
        return result

    async def reading_types(self, user_id):
        rows = await self.db.execute(
            select(LearningSignal.concept_key, LearningSignal.outcome, func.count())
            .where(
                LearningSignal.user_id == user_id,
                LearningSignal.skill == "READING",
                LearningSignal.active.is_(True),
            )
            .group_by(LearningSignal.concept_key, LearningSignal.outcome)
        )
        groups = defaultdict(Counter)
        for key, outcome, count in rows:
            groups[key][outcome] = count
        return [
            {
                "concept_key": key,
                "label": label(key),
                "total": sum(c.values()),
                "correct": c["SUCCESS"],
                "incorrect": c["ERROR"],
                "accuracy": round(c["SUCCESS"] / sum(c.values()) * 100, 1),
            }
            for key, c in groups.items()
        ]

    async def strengths(self, user_id):
        strengths = []
        for skill in ("WRITING", "SPEAKING"):
            data = await self.skill(user_id, skill)
            for c in data["criteria"]:
                if c["samples"] >= 3 and c["recent_average"] >= 7 and c["trend"] != "DECLINING":
                    strengths.append(
                        {
                            "skill": skill,
                            "label": c["criterion"],
                            "value": c["recent_average"],
                            "unit": "/10",
                            "evidence_count": c["samples"],
                            "trend": c["trend"],
                        }
                    )
        for c in await self.reading_types(user_id):
            if c["total"] >= 10 and c["accuracy"] >= 80:
                strengths.append(
                    {
                        "skill": "READING",
                        "label": c["label"],
                        "value": c["accuracy"],
                        "unit": "%",
                        "evidence_count": c["total"],
                        "trend": "INSUFFICIENT_DATA",
                    }
                )
        return strengths

    async def overview(self, user_id):
        since = utcnow() - timedelta(days=30)
        profile = await self.db.scalar(
            select(UserLearningProfile).where(UserLearningProfile.user_id == user_id)
        )
        counts = dict(
            (
                await self.db.execute(
                    select(LearningAttempt.skill, func.count())
                    .where(LearningAttempt.user_id == user_id, LearningAttempt.occurred_at >= since)
                    .group_by(LearningAttempt.skill)
                )
            ).all()
        )
        reading = await self.db.scalar(
            select(func.count())
            .select_from(LearningSignal)
            .where(
                LearningSignal.user_id == user_id,
                LearningSignal.skill == "READING",
                LearningSignal.active.is_(True),
                LearningSignal.created_at >= since,
            )
        )
        weaknesses = (await self.weaknesses(user_id))["items"]
        return {
            "analysis_version": ANALYSIS_VERSION,
            "revision": profile.revision if profile else 0,
            "backfill_status": profile.backfill_status if profile else "PENDING",
            "backfill_processed": profile.backfill_processed if profile else 0,
            "recent": {
                "writing_attempts": counts.get("WRITING", 0),
                "speaking_attempts": counts.get("SPEAKING", 0),
                "reading_questions": reading,
            },
            "top_priorities": [w for w in weaknesses if w["status"] != "MASTERED"][:3],
            "improving_skills": len(
                {s for w in weaknesses if w["trend"] == "IMPROVING" for s in w["stats"].get("skills", [])}
            ),
            "mastered_count": sum(w["status"] == "MASTERED" for w in weaknesses),
            "strengths": await self.strengths(user_id),
            "weekly": await self.weekly(user_id, weaknesses),
            "priority_note_vi": "Ưu tiên học dựa trên bằng chứng, mức độ lặp lại và độ gần đây; đây không phải công thức tính điểm VSTEP.",
        }

    async def weekly(self, user_id, weaknesses=None):
        from app.learning.weekly import cached_summary

        since = utcnow() - timedelta(days=7)
        if weaknesses is None:
            weaknesses = (await self.weaknesses(user_id))["items"]
        attempts = await self.db.scalar(
            select(func.count())
            .select_from(LearningAttempt)
            .where(LearningAttempt.user_id == user_id, LearningAttempt.occurred_at >= since)
        )
        seconds = await self.db.scalar(
            select(func.sum(LearningExerciseAnswer.duration_seconds)).where(
                LearningExerciseAnswer.user_id == user_id, LearningExerciseAnswer.created_at >= since
            )
        )
        changes = [
            w for w in weaknesses if w["trend"] == "IMPROVING" and w["stats"].get("older_rate") is not None
        ]
        best = max(
            changes,
            key=lambda w: (
                (w["stats"]["older_rate"] - w["stats"]["recent_rate"]) / max(0.001, w["stats"]["older_rate"])
            ),
            default=None,
        )
        return {
            "attempts_completed": attempts,
            "recorded_practice_minutes": round((seconds or 0) / 60),
            "new_weaknesses": sum(w["first_seen_at"] >= since for w in weaknesses),
            "improving": sum(w["trend"] == "IMPROVING" for w in weaknesses),
            "mastered": sum(w["status"] == "MASTERED" for w in weaknesses),
            "highest_improvement": best["display_name_vi"] if best else None,
            "next_priority": next(
                (w["display_name_vi"] for w in weaknesses if w["status"] != "MASTERED"), None
            ),
            "ai_summary": await cached_summary(self.db, user_id),
        }

    async def vocabulary(self, user_id):
        attempts = list(
            await self.db.scalars(
                select(LearningAttempt)
                .where(LearningAttempt.user_id == user_id, LearningAttempt.skill.in_(["WRITING", "SPEAKING"]))
                .order_by(LearningAttempt.occurred_at.desc())
                .limit(30)
            )
        )
        totals, affected = Counter(), Counter()
        for a in attempts:
            totals.update(a.lexical_counts)
            affected.update(a.lexical_counts.keys())
        notebook = list(
            await self.db.scalars(
                select(UserVocabularyItem)
                .where(UserVocabularyItem.user_id == user_id)
                .order_by(UserVocabularyItem.last_reviewed_at.desc().nullslast())
                .limit(100)
            )
        )
        events = list(
            await self.db.scalars(
                select(UserLearningEvent).where(
                    UserLearningEvent.user_id == user_id,
                    UserLearningEvent.event_type.in_(["CONCEPT_REUSED", "VOCABULARY_OBSERVED"]),
                )
            )
        )
        active_versions = {
            a.source_version
            for a in await self.db.scalars(select(LearningAttempt).where(LearningAttempt.user_id == user_id))
        }
        usage = defaultdict(list)
        for e in events:
            if e.details.get("item_id") and e.details.get("source_version") in active_versions:
                usage[e.details["item_id"]].append(e)
        return {
            "weaknesses": (await self.weaknesses(user_id, category="VOCABULARY"))["items"],
            "frequent_expressions": [
                {"phrase": p, "count": c, "attempts": affected[p]}
                for p, c in totals.most_common(20)
                if affected[p] >= 2
            ],
            "frequency_note_vi": "Tần suất là gợi ý xem lại ngữ cảnh, không tự động được coi là lỗi. Từ chức năng đã được bỏ qua.",
            "notebook": [
                {
                    "id": i.id,
                    "phrase": i.phrase,
                    "mastery_level": i.mastery_level,
                    "review_count": i.review_count,
                    "observed_reuses": len(usage[i.id]),
                    "verified_reuses": sum(e.details.get("verified", False) for e in usage[i.id]),
                    "pending_verifications": [
                        e.id
                        for e in usage[i.id]
                        if not e.details.get("verified")
                        and not e.details.get("assessment")
                        and e.details.get("sentence")
                    ],
                    "skills": sorted({e.skill for e in usage[i.id]}),
                    "learned_not_reused": i.review_count > 0 and not usage[i.id],
                }
                for i in notebook
            ],
            "notebook_url": "/vocabulary",
        }
