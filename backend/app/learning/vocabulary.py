from sqlalchemy import select

from app.common.errors import AppError
from app.core.config import settings
from app.db.session import SessionLocal
from app.learning import ANALYSIS_VERSION, TAXONOMY_VERSION
from app.learning.aggregation import WeaknessAggregationService
from app.learning.extraction import digest
from app.learning.signals import profile_for
from app.learning.taxonomy import normalize
from app.models.learning import LearningAttempt, LearningSignal, UserLearningEvent
from app.models.vocabulary import UserVocabularyItem, VocabularyReview
from app.services.speech_transcription_service import speech_lock


async def record_vocabulary_review(db, review, item):
    if not review.assessed_at:
        return
    key = f"vocabulary-review:{review.id}"
    if await db.scalar(
        select(UserLearningEvent.id).where(
            UserLearningEvent.user_id == review.user_id, UserLearningEvent.dedup_key == key
        )
    ):
        return
    _, _, concept = normalize(
        "vocabulary", item.issue_type, item.user_original_text or "", item.improved_text or ""
    )
    db.add(
        UserLearningEvent(
            user_id=review.user_id,
            skill="CROSS",
            concept_key=concept,
            event_type="EXERCISE_CORRECT"
            if review.correct is True
            else "EXERCISE_INCORRECT"
            if review.correct is False
            else "EXERCISE_ATTEMPTED",
            source_exercise_id=review.id,
            dedup_key=key,
            created_at=review.assessed_at,
            details={
                "item_id": item.id,
                "phrase": item.phrase,
                "verified": review.correct is not None,
                "source": "vocabulary_coach",
            },
        )
    )


async def sync_vocabulary_learning(user_id, review_id):
    async with SessionLocal() as db:
        await speech_lock(db, f"learning:{user_id}")
        review = await db.scalar(
            select(VocabularyReview).where(
                VocabularyReview.user_id == user_id, VocabularyReview.id == review_id
            )
        )
        if not review:
            return
        item = await db.scalar(
            select(UserVocabularyItem).where(
                UserVocabularyItem.id == review.item_id, UserVocabularyItem.user_id == user_id
            )
        )
        if not item:
            return
        await record_vocabulary_review(db, review, item)
        await db.flush()
        await WeaknessAggregationService(db).aggregate(user_id)
        (await profile_for(db, user_id)).revision += 1
        await db.commit()


async def verify_reuse(db, llm, user_id, event_id):
    event = await db.scalar(
        select(UserLearningEvent)
        .where(UserLearningEvent.id == event_id, UserLearningEvent.user_id == user_id)
        .with_for_update()
    )
    if not event or not event.details.get("item_id"):
        raise AppError(404, "Không tìm thấy bằng chứng dùng từ.")
    attempt = await db.scalar(
        select(LearningAttempt).where(
            LearningAttempt.user_id == user_id,
            LearningAttempt.skill == event.skill,
            LearningAttempt.attempt_id == event.source_attempt_id,
        )
    )
    if not attempt or attempt.source_version != event.details.get("source_version"):
        raise AppError(409, "Bài đã được chấm lại. Hãy cập nhật hồ sơ học tập.")
    if event.details.get("assessment") or event.details.get("verified"):
        return event.details
    item = await db.scalar(
        select(UserVocabularyItem).where(
            UserVocabularyItem.id == event.details["item_id"], UserVocabularyItem.user_id == user_id
        )
    )
    sentence = event.details.get("sentence")
    if not item or not sentence:
        raise AppError(409, "Chưa có câu gốc để kiểm tra cách dùng.")
    result = await llm.assess_vocabulary_usage(
        {
            "phrase": item.phrase,
            "meaning_vi": item.meaning_vi,
            "meaning_in_context_vi": item.meaning_in_context_vi,
            "patterns": item.common_patterns,
            "sentence": sentence,
        },
        user_id,
    )
    correct = result.correct if result.confidence >= 0.8 else None
    event.details = {
        **event.details,
        "verified": correct is True,
        "assessment": result.model_dump(),
        "model": settings.openai_model,
    }
    event.event_type = "CONCEPT_REUSED" if correct is True else "VOCABULARY_OBSERVED"
    cat, sub, concept = normalize(
        "vocabulary", item.issue_type, item.user_original_text or "", item.improved_text or ""
    )
    if correct is True:
        # The exact historical sentence is evaluated, never a fabricated learner answer.
        db.add(
            LearningSignal(
                user_id=user_id,
                attempt_id=attempt.attempt_id,
                skill=attempt.skill,
                category=cat,
                subcategory=sub,
                concept_key=concept,
                original_text=sentence,
                corrected_text=None,
                severity="minor",
                confidence=result.confidence,
                outcome="SUCCESS",
                created_at=event.created_at,
                fingerprint=digest(["vocabulary-transfer", event.id]),
                source_version=attempt.source_version,
                grader_version="vocabulary-usage-1",
                analysis_version=ANALYSIS_VERSION,
                taxonomy_version=TAXONOMY_VERSION,
                model=settings.openai_model,
                details={
                    "item_id": item.id,
                    "source_url": attempt.source_url,
                    "context_hash": digest(sentence),
                    "evidence_kind": "verified_vocabulary_usage",
                    "explanation_vi": result.explanation_vi,
                },
            )
        )
    await speech_lock(db, f"learning:{user_id}")
    await db.flush()
    await WeaknessAggregationService(db).aggregate(user_id)
    (await profile_for(db, user_id)).revision += 1
    await db.commit()
    return event.details
