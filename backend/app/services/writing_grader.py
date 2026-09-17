import hashlib
import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.common.errors import AppError
from app.core.config import settings
from app.db.base import utcnow
from app.models import WritingAttempt, WritingError, WritingGrading
from app.models.assessment import WritingGradingRevision
from app.prompts.writing_analysis import (
    WRITING_ANALYSIS_PROMPT_VERSION,
    WRITING_FEEDBACK_PROMPT_VERSION,
    WRITING_GRADER_VERSION,
)
from app.prompts.writing_calibration import WRITING_CALIBRATION_PROMPT_VERSION
from app.repositories.writing import owned_attempt
from app.schemas.writing_assessment import CRITERIA
from app.services.speech_transcription_service import speech_lock
from app.services.writing_analysis_service import WritingAnalysisService
from app.services.writing_score_calibration_service import WritingScoreCalibrationService

JSON_FIELDS = (
    "strengths",
    "priority_improvements",
    "structure_feedback",
    "task_fulfillment_feedback",
    "vocabulary_suggestions",
    "sentence_feedback",
)
TEXT_FIELDS = ("summary_vi", "corrected_version", "improved_b2_version")
SCORES = (*CRITERIA, "overall")
VERSION_FIELDS = (
    "grader_version",
    "analysis_prompt_version",
    "calibration_prompt_version",
    "criterion_evidence",
    "analysis_snapshot",
)


class WritingGradingService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def _locked(self, attempt_id, user_id):
        await owned_attempt(self.db, attempt_id, user_id)
        await speech_lock(self.db, f"writing-assessment:{user_id}:{attempt_id}")
        attempt = await self.db.scalar(
            select(WritingAttempt)
            .where(WritingAttempt.id == attempt_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if attempt.status == "DRAFT":
            raise AppError(409, "Vui lòng nộp bài trước khi chấm.", "not_submitted")
        return attempt

    def _payload(self, attempt):
        q = attempt.question
        return {
            "task": q.task_type,
            "question_type": q.question_type,
            "question": q.instruction,
            "requirements": q.requirements,
            "minimum_words": q.minimum_words,
            "user_answer": attempt.answer,
            "word_count": attempt.word_count,
        }

    def _work(self, attempt):
        payload = self._payload(attempt)
        key = hashlib.sha256(
            json.dumps(
                {
                    "payload": payload,
                    "model": settings.openai_model,
                    "grader": WRITING_GRADER_VERSION,
                    "analysis": WRITING_ANALYSIS_PROMPT_VERSION,
                    "calibration": WRITING_CALIBRATION_PROMPT_VERSION,
                    "feedback": WRITING_FEEDBACK_PROMPT_VERSION,
                    "temperature": settings.openai_grading_temperature,
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        work = dict(attempt.grading_work or {})
        if work.get("cache_key") != key:
            work = {"cache_key": key, "grader_version": WRITING_GRADER_VERSION}
        return payload, work

    def _preserve(self, attempt, upgrade):
        return attempt.grading and (not upgrade or attempt.grading.grader_version == WRITING_GRADER_VERSION)

    async def analyze(self, attempt_id, user_id, upgrade=False):
        attempt = await self._locked(attempt_id, user_id)
        if self._preserve(attempt, upgrade):
            await self.db.commit()
            return {"stage": "complete", "reviewed": True}
        payload, work = self._work(attempt)
        if not work.get("analysis"):
            cached = await self.db.scalar(
                select(WritingGrading)
                .join(WritingAttempt)
                .where(WritingAttempt.user_id == user_id, WritingGrading.cache_key == work["cache_key"])
                .limit(1)
            )
            if cached and cached.analysis_snapshot:
                work["analysis"] = cached.analysis_snapshot
                work["calibration"] = {
                    "assessment": cached.criterion_evidence,
                    "reviewed": True,
                    "consistency_flags": [],
                }
            else:
                work["analysis"] = await WritingAnalysisService(self.llm).analyze(payload, user_id)
            attempt.grading_work = work
        await self.db.commit()
        return {"stage": "analyzed", "reviewed": bool(work.get("calibration", {}).get("reviewed"))}

    async def calibrate(self, attempt_id, user_id, upgrade=False):
        await self.analyze(attempt_id, user_id, upgrade)
        attempt = await self._locked(attempt_id, user_id)
        if self._preserve(attempt, upgrade):
            await self.db.commit()
            return {"stage": "complete", "reviewed": True}
        _, work = self._work(attempt)
        current = work.get("calibration")
        if not current or not current["reviewed"]:
            work["calibration"] = await WritingScoreCalibrationService(self.llm).calibrate(
                work["analysis"], user_id, current["assessment"] if current else None
            )
            attempt.grading_work = work
        await self.db.commit()
        return {"stage": "calibrated", "reviewed": work["calibration"]["reviewed"]}

    async def grade(self, attempt_id, user_id, upgrade=False):
        state = await self.calibrate(attempt_id, user_id, upgrade)
        if not state["reviewed"]:
            await self.calibrate(attempt_id, user_id, upgrade)
        attempt = await self._locked(attempt_id, user_id)
        if self._preserve(attempt, upgrade):
            await self.db.commit()
            return attempt
        payload, work = self._work(attempt)
        assessment = work["calibration"]["assessment"]
        cached = await self.db.scalar(
            select(WritingGrading)
            .join(WritingAttempt)
            .where(WritingAttempt.user_id == user_id, WritingGrading.cache_key == work["cache_key"])
            .limit(1)
        )
        if cached:
            values = {
                key: getattr(cached, key)
                for key in (*JSON_FIELDS, *TEXT_FIELDS, *VERSION_FIELDS, "ai_model", "prompt_version")
            }
            values.update({f"{key}_score": getattr(cached, f"{key}_score") for key in SCORES})
            errors = [
                {
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
                for e in cached.errors
            ]
        else:
            # Feedback is generated only after scores are fixed and cannot change those scores.
            feedback = await self.llm.writing_feedback(
                {**payload, "analysis": work["analysis"], "calibrated_assessment": assessment}, user_id
            )
            values = feedback.model_dump()
            values.update({f"{key}_score": assessment[key]["score"] for key in CRITERIA})
            values.update(
                overall_score=sum(assessment[key]["score"] for key in CRITERIA) / 4,
                ai_model=settings.openai_model,
                prompt_version=WRITING_FEEDBACK_PROMPT_VERSION,
                grader_version=WRITING_GRADER_VERSION,
                analysis_prompt_version=WRITING_ANALYSIS_PROMPT_VERSION,
                calibration_prompt_version=WRITING_CALIBRATION_PROMPT_VERSION,
                criterion_evidence=assessment,
                analysis_snapshot=work["analysis"],
            )
            errors = [
                {
                    "category": e["category"],
                    "subtype": e["subtype"],
                    "original_text": e["original"],
                    "corrected_text": e["corrected"],
                    "explanation_vi": e["explanation_vi"],
                    "severity": e["severity"],
                }
                for e in work["analysis"]["evidence"]["errors"]
            ]
        grading = attempt.grading
        if grading:
            from app.api.serializers import grading_view

            self.db.add(
                WritingGradingRevision(
                    attempt_id=attempt.id,
                    grader_version=grading.grader_version,
                    grading_model=grading.ai_model,
                    snapshot=jsonable_encoder(grading_view(grading)),
                )
            )
            grading.created_at = utcnow()
        else:
            grading = WritingGrading(attempt_id=attempt.id)
        for key, value in values.items():
            setattr(grading, key, value)
        grading.cache_key = work["cache_key"]
        grading.errors = [WritingError(**e) for e in errors]
        attempt.grading, attempt.status = grading, "GRADED"
        self.db.add(grading)
        await self.db.commit()
        return attempt
