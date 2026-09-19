from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.base import utcnow
from app.learning.taxonomy import label
from app.models.learning import LearningAttempt, LearningSignal, UserLearningEvent, UserWeakness

SEVERITY = {"minor": 1, "major": 2, "critical": 3}


def trend_from_rates(older, recent, *, higher_is_better=False):
    if older is None or recent is None:
        return "INSUFFICIENT_DATA"
    delta = recent - older
    if not higher_is_better:
        delta = -delta
    threshold = max(0.05, abs(older) * settings.learning_trend_delta)
    return "IMPROVING" if delta > threshold else "DECLINING" if delta < -threshold else "STABLE"


def evidence_trend(signals, attempts, category, skill):
    """Compare disjoint attempt windows with exposure denominators, including zero errors."""
    relevant = [
        a for a in attempts if a.skill == skill or skill == "CROSS" and a.skill in {"WRITING", "SPEAKING"}
    ]
    if skill == "READING":
        ids = {s.attempt_id for s in signals}
        relevant = [a for a in relevant if a.attempt_id in ids]
    if category in {"PRONUNCIATION", "FLUENCY"}:
        criterion = "pronunciation" if category == "PRONUNCIATION" else "fluency"
        relevant = [a for a in relevant if a.scores.get(criterion) is not None]
    relevant.sort(key=lambda a: a.occurred_at)
    window = settings.learning_trend_window
    if len(relevant) < window * 2:
        return {
            "trend": "INSUFFICIENT_DATA",
            "older_rate": None,
            "recent_rate": None,
            "window_attempts": window,
            "unit": "tỷ lệ câu sai"
            if skill == "READING"
            else "lỗi / 100 từ"
            if category in {"GRAMMAR", "VOCABULARY"}
            else "lần / bài",
        }

    def rate(group):
        ids = {(a.skill, a.attempt_id) for a in group}
        rows = [s for s in signals if (s.skill, s.attempt_id) in ids]
        errors = sum(s.outcome == "ERROR" for s in rows)
        if skill == "READING":
            return errors / max(1, len(rows))
        if category in {"GRAMMAR", "VOCABULARY"}:
            return errors * 100 / max(1, sum(a.exposure for a in group))
        return errors / len(group)

    older, recent = rate(relevant[-window * 2 : -window]), rate(relevant[-window:])
    return {
        "trend": trend_from_rates(older, recent),
        "older_rate": round(older, 3),
        "recent_rate": round(recent, 3),
        "window_attempts": window,
        "unit": "tỷ lệ câu sai"
        if skill == "READING"
        else "lỗi / 100 từ"
        if category in {"GRAMMAR", "VOCABULARY"}
        else "lần / bài",
    }


def priority_score(errors, confidence, category, trend, now):
    weights = settings.learning_priority_weights
    weighted = sum(
        2 ** (-max(0, (now - s.created_at).days) / settings.learning_recency_half_life_days) for s in errors
    )
    factors = {
        "frequency": min(1, weighted / 10),
        "recency": 2
        ** (
            -max(0, (now - max(s.created_at for s in errors)).days) / settings.learning_recency_half_life_days
        ),
        "severity": max(SEVERITY.get(s.severity, 1) for s in errors) / 3,
        "confidence": confidence,
        "impact": 1 if category in {"TASK_FULFILLMENT", "COMPREHENSION", "GRAMMAR"} else 0.8,
        "persistence": 1
        if trend == "DECLINING"
        else 0.7
        if trend == "STABLE"
        else 0.4
        if trend == "INSUFFICIENT_DATA"
        else 0.15,
    }
    return round(sum(weights.get(k, 0) * v for k, v in factors.items()), 1)


def mastery_state(errors, signals, events, trend, previous_status):
    attempts = len({(s.skill, s.attempt_id) for s in errors})
    base = (
        "RECURRING"
        if attempts >= settings.learning_recurring_attempts
        else "OBSERVED"
        if attempts >= settings.learning_observed_attempts
        else "NEW"
    )
    exercises = sorted(
        [e for e in events if e.event_type in {"EXERCISE_CORRECT", "EXERCISE_INCORRECT"}],
        key=lambda e: e.created_at,
    )[-40:]
    accuracy = (
        sum(e.event_type == "EXERCISE_CORRECT" for e in exercises) / len(exercises) if exercises else None
    )
    sessions = len({e.source_exercise_id for e in exercises})
    days = len({e.created_at.date() for e in exercises})
    last_error = max((s.created_at for s in errors), default=None)
    reuses = [
        s for s in signals if s.outcome == "SUCCESS" and (last_error is None or s.created_at > last_error)
    ]
    contexts = {s.details.get("context_hash") or (s.original_text or "").casefold() for s in reuses}
    reuse_attempts = len({s.attempt_id for s in reuses})
    practiced = bool(exercises)
    viewed = any(e.event_type == "LESSON_VIEWED" for e in events)
    qualified = (
        len(exercises) >= settings.learning_mastery_exercises
        and sessions >= settings.learning_mastery_sessions
        and days >= 2
        and accuracy is not None
        and accuracy >= 0.85
        and reuse_attempts >= settings.learning_mastery_reuses
        and len(contexts) >= settings.learning_mastery_reuses
    )
    if qualified:
        return "MASTERED", "MASTERED", accuracy, reuse_attempts
    mastered_events = [e for e in events if e.event_type == "CONCEPT_MASTERED"]
    if mastered_events:
        mastered_at = max(e.created_at for e in mastered_events)
        new_errors = {(s.skill, s.attempt_id) for s in errors if s.created_at > mastered_at}
        if len(new_errors) >= 2:
            return "REGRESSED", "LEARNING", accuracy, reuse_attempts
        if previous_status == "MASTERED" and not new_errors:
            return "MASTERED", "MASTERED", accuracy, reuse_attempts
    if trend == "IMPROVING" or (len(exercises) >= 5 and accuracy >= 0.8 and reuse_attempts >= 1):
        return "IMPROVING", "IMPROVING", accuracy, reuse_attempts
    return (
        ("LEARNING" if viewed or practiced else base),
        ("PRACTICING" if practiced else "LEARNING" if viewed else "NOT_STARTED"),
        accuracy,
        reuse_attempts,
    )


class WeaknessAggregationService:
    def __init__(self, db):
        self.db = db

    async def aggregate(self, user_id):
        signals = list(
            await self.db.scalars(
                select(LearningSignal).where(
                    LearningSignal.user_id == user_id, LearningSignal.active.is_(True)
                )
            )
        )
        attempts = list(
            await self.db.scalars(select(LearningAttempt).where(LearningAttempt.user_id == user_id))
        )
        events = list(
            await self.db.scalars(select(UserLearningEvent).where(UserLearningEvent.user_id == user_id))
        )
        existing = {
            (w.skill, w.concept_key): w
            for w in await self.db.scalars(select(UserWeakness).where(UserWeakness.user_id == user_id))
        }
        groups = defaultdict(list)
        for s in signals:
            # A shared concept has one canonical aggregate, with per-skill evidence in stats.
            skill = "CROSS" if s.category in {"GRAMMAR", "VOCABULARY"} else s.skill
            groups[(skill, s.concept_key)].append(s)
        now = utcnow()
        for key, rows in groups.items():
            errors = [s for s in rows if s.outcome == "ERROR"]
            if not errors:
                continue
            first = min(errors, key=lambda s: s.created_at)
            last = max(errors, key=lambda s: s.created_at)
            affected = len({(s.skill, s.attempt_id) for s in errors})
            skills = sorted({s.skill for s in errors})
            confidence = min(
                0.98,
                (0.35 if affected == 1 else 0.6 if affected == 2 else 0.8 if affected < 6 else 0.9)
                + (0.08 if len(skills) > 1 else 0),
            )
            confidence = min(confidence, sum(s.confidence for s in errors) / len(errors))
            trend = evidence_trend(rows, attempts, first.category, key[0])
            w = existing.get(key) or UserWeakness(user_id=user_id, skill=key[0], concept_key=key[1])
            old = w.status
            related_events = [e for e in events if e.concept_key == key[1]]
            status, mastery, accuracy, reuse_attempts = mastery_state(
                errors, rows, related_events, trend["trend"], old
            )
            w.category, w.subcategory = first.category, first.subcategory
            w.display_name_vi, w.display_name_en = label(key[1]), key[1].replace("_", " ").title()
            w.occurrence_count, w.affected_attempt_count = len(errors), affected
            w.recent_occurrence_count = sum(s.created_at >= now - timedelta(days=30) for s in errors)
            w.first_seen_at, w.last_seen_at = first.created_at, last.created_at
            w.severity = max(errors, key=lambda s: SEVERITY.get(s.severity, 1)).severity
            w.confidence, w.status, w.mastery_status, w.trend = confidence, status, mastery, trend["trend"]
            w.priority_score = (
                0 if status == "MASTERED" else priority_score(errors, confidence, w.category, w.trend, now)
            )
            practice_events = [e for e in related_events if e.event_type.startswith("EXERCISE_")]
            successes = [s.created_at for s in rows if s.outcome == "SUCCESS"] + [
                e.created_at for e in practice_events if e.event_type == "EXERCISE_CORRECT"
            ]
            w.last_practiced_at = max((e.created_at for e in practice_events), default=None)
            w.last_success_at = max(successes, default=None)
            w.stats = {
                **trend,
                "skills": skills,
                "by_skill": {s: sum(r.outcome == "ERROR" and r.skill == s for r in rows) for s in skills},
                "accuracy": round(sum(r.outcome == "SUCCESS" for r in rows) / len(rows) * 100, 1)
                if key[0] == "READING"
                else None,
                "question_count": len(rows) if key[0] == "READING" else None,
                "exercise_accuracy": round(accuracy * 100, 1) if accuracy is not None else None,
                "exercise_count": len(practice_events),
                "reuse_attempts": reuse_attempts,
                "confidence_label": "ít bằng chứng"
                if affected == 1
                else "đang hình thành"
                if affected == 2
                else "lặp lại"
                if affected < 6
                else "bằng chứng rõ",
                "evidence_active": True,
            }
            self.db.add(w)
            if status in {"MASTERED", "REGRESSED"} and old != status:
                self.db.add(
                    UserLearningEvent(
                        user_id=user_id,
                        skill=key[0],
                        event_type="CONCEPT_" + status,
                        concept_key=key[1],
                        dedup_key=f"state:{w.id or key[1]}:{status}:{now.isoformat()}",
                        details={"previous_status": old},
                    )
                )
        # Regrading may remove a diagnosis. Retain its history without recommending stale errors.
        for key, w in existing.items():
            if key not in groups or not any(s.outcome == "ERROR" for s in groups[key]):
                w.occurrence_count = w.affected_attempt_count = w.recent_occurrence_count = 0
                w.priority_score = 0
                w.stats = {**w.stats, "evidence_active": False}
        await self.db.flush()
