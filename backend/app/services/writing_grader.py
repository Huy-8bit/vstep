import copy
import hashlib
import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.common.errors import AppError
from app.core.config import settings
from app.db.base import utcnow
from app.learning.signals import sync_learning
from app.llm.routing import route_for
from app.llm.usage import ai_context
from app.models import WritingAttempt, WritingError, WritingGrading
from app.models.assessment import WritingGradingRevision
from app.prompts.writing_analysis import WRITING_GRADER_VERSION
from app.prompts.writing_core import WRITING_CORE_VERSION
from app.repositories.writing import owned_attempt
from app.schemas.writing_assessment import CRITERIA
from app.services.grading_escalation_service import ESCALATION_VERSION, GradingEscalationService
from app.services.speech_transcription_service import speech_lock
from app.services.vocabulary_coach_service import VocabularyCoachService
from app.services.writing_core_service import WritingCoreService
from app.services.writing_feedback_service import WritingFeedbackService

JSON_FIELDS = (
    "strengths",
    "priority_improvements",
    "structure_feedback",
    "task_fulfillment_feedback",
    "vocabulary_suggestions",
    "sentence_feedback",
)
TEXT_FIELDS = ("summary_vi", "corrected_version", "improved_b2_version")
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
            "question": "\n\n".join(filter(None, [q.instruction, q.stimulus, q.response_instruction])),
            "communicative_context": {
                "register": q.register,
                "recipient_relationship": q.recipient_relationship,
                "purpose": q.purpose,
                "genre": q.genre,
            },
            "requirements": q.requirements,
            "minimum_words": q.minimum_words,
            "user_answer": attempt.answer,
            "word_count": attempt.word_count,
        }

    def _work(self, attempt):
        payload = self._payload(attempt)
        identity = {
            "payload": payload,
            "routes": {
                op: route_for(op).identity
                for op in ("writing_core", "writing_calibration", "writing_escalation")
            },
            "grader": WRITING_GRADER_VERSION,
            "model_version": settings.model_version,
            "prompt": WRITING_CORE_VERSION,
            "temperature": settings.openai_grading_temperature,
            "escalation_version": ESCALATION_VERSION,
            "escalation_enabled": settings.grading_escalation_enabled,
            "confidence": settings.grading_confidence_threshold,
            "boundary_confidence": settings.grading_boundary_confidence_threshold,
            "long_words": settings.grading_long_response_words,
        }
        key = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        work = copy.deepcopy(attempt.grading_work or {})
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
        await speech_lock(self.db, f"writing-content:{user_id}:{work['cache_key']}")
        if not work.get("analysis"):
            # Reuse a completed core snapshot even if its result page has not yet published the grade.
            cached = await self.db.scalar(
                select(WritingAttempt.grading_work)
                .where(
                    WritingAttempt.user_id == user_id,
                    WritingAttempt.grading_work["cache_key"].astext == work["cache_key"],
                    WritingAttempt.grading_work["calibration"]["reviewed"].as_boolean().is_(True),
                )
                .limit(1)
            )
            if cached:
                work = copy.deepcopy(
                    {
                        k: cached[k]
                        for k in (
                            "cache_key",
                            "grader_version",
                            "analysis",
                            "calibration",
                            "feedback",
                            "routing",
                            "model",
                        )
                    }
                )
                work["cache_reused"] = True
            else:
                checker = GradingEscalationService()
                primary = None
                primary_model = route_for("writing_core").model
                with ai_context(attempt_id=attempt_id):
                    try:
                        primary = await WritingCoreService(self.llm).analyze(payload, user_id)
                        # Separate scoring is an explicit opt-in. Check its result before routing review.
                        if route_for("writing_calibration").identity != route_for("writing_core").identity:
                            from app.services.writing_score_calibration_service import (
                                WritingScoreCalibrationService,
                            )

                            separate = await WritingScoreCalibrationService(self.llm).calibrate(
                                primary["analysis"], user_id
                            )
                            primary["assessment"] = separate["assessment"]
                            primary_model = route_for("writing_calibration").model
                        reasons = checker.writing_reasons(primary)
                    except AppError as exc:
                        if exc.code != "ai_invalid_output" or not settings.grading_escalation_enabled:
                            raise
                        reasons = ["INVALID_PRIMARY_OUTPUT"]
                    final = primary
                    final_model = primary_model
                    if reasons and settings.grading_escalation_enabled:
                        final = await WritingCoreService(self.llm).analyze(
                            checker.writing_review_payload(payload, primary, reasons),
                            user_id,
                            "writing_escalation",
                        )
                        final_model = route_for("writing_escalation").model
                    if final is None:
                        raise AppError(
                            502, "Chưa có kết quả chấm hợp lệ. Bài viết đã được lưu.", "ai_invalid_output"
                        )
                    work.update(
                        analysis=final["analysis"],
                        feedback=final["feedback"],
                        calibration={
                            "assessment": final["assessment"],
                            "reviewed": True,
                            "consistency_flags": checker.writing_reasons(final),
                        },
                        routing={
                            "primary_model": route_for("writing_core").model,
                            "final_model": final_model,
                            "reasoning_effort": route_for(
                                "writing_escalation"
                                if reasons and settings.grading_escalation_enabled
                                else "writing_core"
                            ).reasoning_effort,
                            "escalated": bool(reasons and settings.grading_escalation_enabled),
                            "reasons": reasons,
                            "confidence": final["confidence"],
                            "primary_assessment": primary["assessment"] if primary else None,
                        },
                        model=final_model,
                    )
                    # Development-only shadow never affects the displayed grade or core cache identity.
                    bucket = int(hashlib.sha256(attempt_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
                    if (
                        settings.app_env != "production"
                        and settings.grading_shadow_enabled
                        and bucket < settings.grading_shadow_sample_rate
                    ):
                        try:
                            work["shadow"] = await WritingCoreService(self.llm).analyze(
                                payload, user_id, "writing_shadow"
                            )
                            work["shadow"]["model"] = route_for("writing_shadow").model
                        except AppError as exc:
                            work["shadow"] = {"error_code": exc.code}
            attempt.grading_work = work
        await self.db.commit()
        return {"stage": "analyzed", "reviewed": True}

    async def calibrate(self, attempt_id, user_id, upgrade=False):
        result = await self.analyze(attempt_id, user_id, upgrade)
        return {**result, "stage": "calibrated"}

    async def grade(self, attempt_id, user_id, upgrade=False):
        await self.calibrate(attempt_id, user_id, upgrade)
        attempt = await self._locked(attempt_id, user_id)
        if self._preserve(attempt, upgrade):
            await self.db.commit()
            await sync_learning(user_id, "WRITING", attempt_id)
            return attempt
        _, work = self._work(attempt)
        assessment = work["calibration"]["assessment"]
        values = {
            **work["feedback"],
            "sentence_feedback": [],
            "corrected_version": "",
            "improved_b2_version": "",
            **{f"{k}_score": assessment[k]["score"] for k in CRITERIA},
            "overall_score": sum(assessment[k]["score"] for k in CRITERIA) / 4,
            "ai_model": work["model"],
            "prompt_version": WRITING_CORE_VERSION,
            "grader_version": WRITING_GRADER_VERSION,
            "analysis_prompt_version": WRITING_CORE_VERSION,
            "calibration_prompt_version": WRITING_CORE_VERSION,
            "criterion_evidence": assessment,
            "analysis_snapshot": work["analysis"],
        }
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
        grading.errors = [
            WritingError(
                category=e["category"],
                subtype=e["subtype"],
                original_text=e["original"],
                corrected_text=e["corrected"],
                explanation_vi=e["explanation_vi"],
                severity=e["severity"],
            )
            for e in work["analysis"]["evidence"]["errors"]
        ]
        attempt.grading, attempt.status = grading, "GRADED"
        self.db.add(grading)
        await self.db.commit()
        await sync_learning(user_id, "WRITING", attempt_id)
        return attempt

    async def prepare_feedback(self, attempt_id, user_id, upgrade=False):
        await self.grade(attempt_id, user_id, upgrade)
        attempt = await self._locked(attempt_id, user_id)
        work = copy.deepcopy(attempt.grading_work or {})
        key = route_for("writing_feedback").identity + ":" + WRITING_CORE_VERSION
        if work.get("detail_feedback_key") != key:
            with ai_context(attempt_id=attempt_id):
                feedback = await WritingFeedbackService(self.llm).feedback(
                    {
                        **self._payload(attempt),
                        "analysis": attempt.grading.analysis_snapshot,
                        "calibrated_assessment": attempt.grading.criterion_evidence,
                    },
                    user_id,
                )
            for name, value in feedback.model_dump().items():
                setattr(attempt.grading, name, value)
            work["detail_feedback_key"] = key
            attempt.grading_work = work
        await self.db.commit()
        return {"stage": "feedback_ready"}

    async def prepare_vocabulary(self, attempt_id, user_id, upgrade=False):
        await self.grade(attempt_id, user_id, upgrade)
        attempt = await self._locked(attempt_id, user_id)
        work = {
            "analysis": attempt.grading.analysis_snapshot,
            "feedback": {"vocabulary_suggestions": attempt.grading.vocabulary_suggestions},
        }
        with ai_context(attempt_id=attempt_id):
            batch = await VocabularyCoachService(self.db, self.llm).prepare_writing(attempt, work, user_id)
        return {"stage": "vocabulary_ready", "batch_id": batch["batch_id"]}
