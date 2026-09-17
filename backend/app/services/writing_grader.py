import hashlib
import json

from sqlalchemy import select, text

from app.common.errors import AppError
from app.core.config import settings
from app.llm.base import LLMClient
from app.models import WritingAttempt, WritingError, WritingGrading
from app.prompts.task1_grader import TASK1_GRADER_PROMPT_VERSION
from app.prompts.task2_grader import TASK2_GRADER_PROMPT_VERSION
from app.repositories.writing import owned_attempt

JSON_FIELDS = (
    "strengths",
    "priority_improvements",
    "structure_feedback",
    "task_fulfillment_feedback",
    "vocabulary_suggestions",
    "sentence_feedback",
)
TEXT_FIELDS = ("summary_vi", "corrected_version", "improved_b2_version")
SCORES = ("task_fulfillment", "organization", "vocabulary", "grammar", "overall")


class WritingGradingService:
    def __init__(self, db, llm: LLMClient):
        self.db = db
        self.llm = llm

    async def grade(self, attempt_id: str, user_id: str):
        attempt = await owned_attempt(self.db, attempt_id, user_id)
        if attempt.status == "DRAFT":
            raise AppError(409, "Vui lòng nộp bài trước khi chấm.", "not_submitted")
        version = TASK1_GRADER_PROMPT_VERSION if attempt.task_type == 1 else TASK2_GRADER_PROMPT_VERSION
        q = attempt.question
        payload = {
            "task": q.task_type,
            "question_type": q.question_type,
            "question": q.instruction,
            "requirements": q.requirements,
            "minimum_words": q.minimum_words,
            "user_answer": attempt.answer,
            "word_count": attempt.word_count,
        }
        cache_key = hashlib.sha256(
            json.dumps(
                {
                    "payload": payload,
                    "model": settings.openai_model,
                    "prompt_version": version,
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        # Serialize all grading for the same learner/content across processes. Transaction-scoped lock
        # is released on both commit and rollback, so failures never leave a stuck GRADING status.
        lock_key = int.from_bytes(hashlib.sha256(f"{user_id}:{cache_key}".encode()).digest()[:8], signed=True)
        await self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
        attempt = await self.db.scalar(
            select(WritingAttempt)
            .where(WritingAttempt.id == attempt_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if attempt.grading:
            return attempt
        cached = await self.db.scalar(
            select(WritingGrading)
            .join(WritingAttempt)
            .where(WritingAttempt.user_id == user_id, WritingGrading.cache_key == cache_key)
            .limit(1)
        )
        if cached:
            grading = WritingGrading(
                attempt_id=attempt.id,
                cache_key=cache_key,
                ai_model=cached.ai_model,
                prompt_version=cached.prompt_version,
                **{f"{key}_score": getattr(cached, f"{key}_score") for key in SCORES},
                **{key: getattr(cached, key) for key in (*JSON_FIELDS, *TEXT_FIELDS)},
            )
            grading.errors = [
                WritingError(
                    **{
                        key: getattr(e, key)
                        for key in (
                            "category",
                            "subtype",
                            "original_text",
                            "corrected_text",
                            "explanation_vi",
                            "severity",
                        )
                    }
                )
                for e in cached.errors
            ]
        else:
            result = await self.llm.grade_writing(payload, user_id)
            # Word count and arithmetic are authoritative application logic, never trusted to the LLM.
            result.word_count = attempt.word_count
            scores = result.scores.model_dump()
            scores["overall"] = sum(scores[key] for key in SCORES[:4]) / 4
            output = result.model_dump()
            grading = WritingGrading(
                attempt_id=attempt.id,
                cache_key=cache_key,
                ai_model=settings.openai_model,
                prompt_version=version,
                **{f"{key}_score": value for key, value in scores.items()},
                **{key: output[key] for key in (*JSON_FIELDS, *TEXT_FIELDS)},
            )
            grading.errors = [
                WritingError(
                    category=e.category,
                    subtype=e.subtype,
                    original_text=e.original,
                    corrected_text=e.corrected,
                    explanation_vi=e.explanation_vi,
                    severity=e.severity,
                )
                for e in result.errors
            ]
        attempt.grading = grading
        attempt.status = "GRADED"
        self.db.add(grading)
        await self.db.commit()
        return attempt
