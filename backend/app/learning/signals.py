import logging
import re

from sqlalchemy import delete, select, update

from app.common.errors import AppError
from app.db.session import SessionLocal
from app.learning import ANALYSIS_VERSION, TAXONOMY_VERSION
from app.learning.aggregation import WeaknessAggregationService
from app.learning.extraction import digest, reading_data, signal, speaking_data, writing_data
from app.models import WritingAttempt
from app.models.learning import LearningAttempt, LearningSignal, UserLearningEvent, UserLearningProfile
from app.models.reading import ReadingExamSession
from app.models.speaking import SpeakingExamSession
from app.models.vocabulary import UserVocabularyItem
from app.services.speech_transcription_service import speech_lock

logger = logging.getLogger(__name__)
SOURCE_MODELS = {"WRITING": WritingAttempt, "SPEAKING": SpeakingExamSession, "READING": ReadingExamSession}
PATTERNS = {
    "ARTICLE": r"\b(?:a|an|the)\s+[a-z][a-z'-]+\b",
    "INTERNET_EXPRESSION": r"\bon the internet\b",
    "ADVANTAGE_COUNTABILITY": r"\bmany advantages\b",
    "AGREE_USAGE": r"\b(?:I|we|they) agree\b",
    "PREPOSITION_INTERESTED_IN": r"\binterested in\b",
    "PREPOSITION_DEPEND_ON": r"\bdepends? on\b",
    "SUBJECT_VERB_AGREEMENT": r"\bpeople (?:are|were|have)\b",
    "GERUND_ENJOY_DOING": r"\benjoy\w* \w+ing\b",
    "INFINITIVE_WANT_TO_DO": r"\bwant\w* to \w+\b",
}


async def profile_for(db, user_id):
    profile = await db.scalar(select(UserLearningProfile).where(UserLearningProfile.user_id == user_id))
    if not profile:
        profile = UserLearningProfile(
            user_id=user_id, analysis_version=ANALYSIS_VERSION, revision=0, backfill_status="PENDING"
        )
        db.add(profile)
        await db.flush()
    return profile


class LearningSignalService:
    def __init__(self, db):
        self.db = db

    async def extract(self, user_id, skill, attempt_id, *, aggregate=True):
        await speech_lock(self.db, f"learning:{user_id}")
        model = SOURCE_MODELS[skill]
        source = await self.db.scalar(select(model).where(model.id == attempt_id, model.user_id == user_id))
        if not source:
            raise AppError(404, "Không tìm thấy bài làm.")
        if skill == "WRITING":
            if not source.grading or source.status != "GRADED":
                return False
            data = writing_data(source)
        elif skill == "SPEAKING":
            if source.mode == "FULL_TEST" and source.status == "IN_PROGRESS":
                return False
            data = speaking_data(source)
            if not data:
                # An explicit practice retake invalidates its former grading snapshot.
                await self.db.execute(
                    update(LearningSignal)
                    .where(
                        LearningSignal.user_id == user_id,
                        LearningSignal.skill == skill,
                        LearningSignal.attempt_id == attempt_id,
                    )
                    .values(active=False)
                )
                removed = await self.db.execute(
                    delete(LearningAttempt).where(
                        LearningAttempt.user_id == user_id,
                        LearningAttempt.skill == skill,
                        LearningAttempt.attempt_id == attempt_id,
                    )
                )
                if removed.rowcount:
                    (await profile_for(self.db, user_id)).revision += 1
                    if aggregate:
                        await WeaknessAggregationService(self.db).aggregate(user_id)
                return False
        else:
            if not source.result or source.status == "IN_PROGRESS":
                return False
            data = reading_data(source)
        version = digest([data["source_version"], ANALYSIS_VERSION, TAXONOMY_VERSION])
        existing = await self.db.scalar(
            select(LearningAttempt).where(
                LearningAttempt.user_id == user_id,
                LearningAttempt.skill == skill,
                LearningAttempt.attempt_id == attempt_id,
            )
        )
        if existing and existing.source_version == version:
            return False
        # Retain old extraction versions for audit, count only the current snapshot.
        await self.db.execute(
            update(LearningSignal)
            .where(
                LearningSignal.user_id == user_id,
                LearningSignal.skill == skill,
                LearningSignal.attempt_id == attempt_id,
            )
            .values(active=False)
        )
        concepts = set(
            await self.db.scalars(
                select(LearningSignal.concept_key)
                .where(
                    LearningSignal.user_id == user_id,
                    LearningSignal.active.is_(True),
                    LearningSignal.outcome == "ERROR",
                    LearningSignal.created_at < data["occurred_at"],
                )
                .distinct()
            )
        )
        for concept, pattern in PATTERNS.items():
            if concept not in concepts or any(s["concept_key"] == concept for s in data["signals"]):
                continue
            # Positive grader evidence plus a known precise grammatical construction is required.
            quote = next(
                (
                    q
                    for q in data["positive_quotes"]
                    if q and q in data["text"] and re.search(pattern, q, re.I)
                ),
                None,
            )
            evidence_kind = "positive_grader_evidence"
            if not quote and skill == "SPEAKING" and concept != "ARTICLE":
                # A precise construction is observable in a graded transcript. Generic absence of an
                # error is insufficient; only the narrow patterns above can supply positive evidence.
                quote = next(
                    (
                        sentence
                        for sentence in re.split(r"(?<=[.!?])\s+|\n", data["text"])
                        if re.search(pattern, sentence, re.I)
                        and not any(
                            s["original_text"] and s["original_text"] in sentence
                            for s in data["signals"]
                            if s["category"] == "GRAMMAR"
                        )
                    ),
                    None,
                )
                evidence_kind = "validated_construction_in_graded_transcript"
            if quote:
                data["signals"].append(
                    signal(
                        "GRAMMAR",
                        concept,
                        quote,
                        outcome="SUCCESS",
                        confidence=0.9,
                        evidence_kind=evidence_kind,
                        context_hash=digest(quote),
                    )
                )
        # Notebook reuse: retain observed usage separately; absence of an error is NOT validated mastery.
        if data["text"]:
            items = await self.db.scalars(
                select(UserVocabularyItem)
                .where(
                    UserVocabularyItem.user_id == user_id,
                    UserVocabularyItem.review_count > 0,
                    UserVocabularyItem.created_at < data["occurred_at"],
                )
                .order_by(UserVocabularyItem.last_reviewed_at.desc())
                .limit(300)
            )
            for item in items:
                if re.search(r"(?<!\w)" + re.escape(item.phrase) + r"(?!\w)", data["text"], re.I):
                    quote = next(
                        (
                            q
                            for q in data["positive_quotes"]
                            if item.phrase.casefold() in q.casefold() and q in data["text"]
                        ),
                        None,
                    )
                    event_key = f"vocab-reuse:{skill}:{attempt_id}:{item.id}:{version[:12]}"
                    if not await self.db.scalar(
                        select(UserLearningEvent.id).where(
                            UserLearningEvent.user_id == user_id, UserLearningEvent.dedup_key == event_key
                        )
                    ):
                        self.db.add(
                            UserLearningEvent(
                                user_id=user_id,
                                skill=skill,
                                concept_key="VOCABULARY_REUSE",
                                event_type="CONCEPT_REUSED" if quote else "VOCABULARY_OBSERVED",
                                source_attempt_id=attempt_id,
                                dedup_key=event_key,
                                created_at=data["occurred_at"],
                                details={
                                    "item_id": item.id,
                                    "phrase": item.phrase,
                                    "verified": bool(quote),
                                    "quote": quote,
                                    "sentence": next(
                                        (
                                            sentence
                                            for sentence in re.split(r"(?<=[.!?])\s+|\n", data["text"])
                                            if item.phrase.casefold() in sentence.casefold()
                                        ),
                                        "",
                                    )[:4000],
                                    "source_version": version,
                                    "source_url": data["source_url"],
                                },
                            )
                        )
        unique = {}
        for s in data["signals"]:
            fp = digest(
                [
                    s["concept_key"],
                    s["original_text"],
                    s["details"].get("offset"),
                    s["details"].get("sentence_id"),
                    s["details"].get("sequence"),
                    s["details"].get("question_id"),
                    s["outcome"],
                ]
            )
            unique[fp] = s
        prior_version_rows = {
            s.fingerprint: s
            for s in await self.db.scalars(
                select(LearningSignal).where(
                    LearningSignal.user_id == user_id,
                    LearningSignal.skill == skill,
                    LearningSignal.attempt_id == attempt_id,
                    LearningSignal.source_version == version,
                )
            )
        }
        for fp, values in unique.items():
            row = prior_version_rows.get(fp)
            if row:
                row.active = True
                continue
            row = LearningSignal(
                user_id=user_id,
                skill=skill,
                attempt_id=attempt_id,
                source_version=version,
                fingerprint=fp,
                grader_version=data["grader_version"],
                analysis_version=ANALYSIS_VERSION,
                taxonomy_version=TAXONOMY_VERSION,
                model=data["model"],
                created_at=data["occurred_at"],
                **{**values, "details": {**values["details"], "source_url": data["source_url"]}},
            )
            self.db.add(row)
            self.db.add(
                UserLearningEvent(
                    user_id=user_id,
                    skill=skill,
                    concept_key=values["concept_key"],
                    event_type="ERROR_DETECTED" if values["outcome"] == "ERROR" else "CONCEPT_REUSED",
                    source_attempt_id=attempt_id,
                    dedup_key=f"signal:{skill}:{attempt_id}:{version[:16]}:{fp[:20]}",
                    created_at=data["occurred_at"],
                    details={"source_version": version, "fingerprint": fp, "verified": True},
                )
            )
        row = existing or LearningAttempt(user_id=user_id, skill=skill, attempt_id=attempt_id)
        for key in ("scores", "exposure", "lexical_counts", "source_url", "occurred_at"):
            setattr(row, key, data[key])
        row.source_version, row.analysis_version = version, ANALYSIS_VERSION
        self.db.add(row)
        if source.status != "IN_PROGRESS":
            from app.learning.transfer import record_attempt_transfers

            await record_attempt_transfers(self.db, user_id, skill, attempt_id, data)
        profile = await profile_for(self.db, user_id)
        profile.revision += 1
        profile.analysis_version = ANALYSIS_VERSION
        await self.db.flush()
        if aggregate:
            await WeaknessAggregationService(self.db).aggregate(user_id)
        return True


async def sync_learning(user_id, skill, attempt_id):
    """Independent transaction: learning errors never undo a successful exam grading."""
    try:
        async with SessionLocal() as db:
            await LearningSignalService(db).extract(user_id, skill, attempt_id)
            await db.commit()
    except Exception:
        logger.exception("Learning extraction deferred: %s", skill)
        # Explicit backfill retries stored grades without calling AI.


async def backfill_learning(user_id):
    try:
        processed = 0
        for skill, model in SOURCE_MODELS.items():
            offset = 0
            while True:
                async with SessionLocal() as db:
                    ids = list(
                        await db.scalars(
                            select(model.id)
                            .where(model.user_id == user_id)
                            .order_by(model.created_at, model.id)
                            .offset(offset)
                            .limit(50)
                        )
                    )
                    if not ids:
                        break
                    for identifier in ids:
                        await LearningSignalService(db).extract(user_id, skill, identifier, aggregate=False)
                        processed += 1
                    profile = await profile_for(db, user_id)
                    profile.backfill_processed = processed
                    await db.commit()
                offset += len(ids)
        async with SessionLocal() as db:
            await speech_lock(db, f"learning:{user_id}")
            from app.learning.vocabulary import record_vocabulary_review
            from app.models.vocabulary import VocabularyReview

            reviews = await db.execute(
                select(VocabularyReview, UserVocabularyItem)
                .join(UserVocabularyItem, UserVocabularyItem.id == VocabularyReview.item_id)
                .where(VocabularyReview.user_id == user_id, VocabularyReview.assessed_at.is_not(None))
            )
            for review, item in reviews:
                await record_vocabulary_review(db, review, item)
            await db.flush()
            await WeaknessAggregationService(db).aggregate(user_id)
            profile = await profile_for(db, user_id)
            profile.backfill_status, profile.backfill_error = "COMPLETE", None
            await db.commit()
    except Exception:
        logger.exception("Learning backfill failed")
        async with SessionLocal() as db:
            profile = await profile_for(db, user_id)
            profile.backfill_status, profile.backfill_error = "FAILED", "retry_required"
            await db.commit()
