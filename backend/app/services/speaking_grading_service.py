import copy
import json

from sqlalchemy import select

from app.common.errors import AppError
from app.core.config import settings
from app.learning.signals import sync_learning
from app.models.speaking import SpeakingError, SpeakingGrading
from app.prompts.speaking_grader import SPEAKING_GRADER_PROMPT_VERSION
from app.services.speaking_correction import SpeakingCorrectionService, speaking_level
from app.services.speaking_exam_service import owned_speaking_answer, owned_speaking_session
from app.services.speech_transcription_service import (
    SpeechTranscriptionService,
    speech_cache_key,
    speech_lock,
)

FEEDBACK_FIELDS = (
    "summary_vi",
    "strengths",
    "priority_improvements",
    "pronunciation_feedback",
    "fluency_feedback",
    "structure_feedback",
    "content_feedback",
    "vocabulary_suggestions",
    "sentence_corrections",
    "answer_feedback",
    "speaking_frame",
    "corrected_transcript",
    "improved_b2_answer",
)
SCORE_FIELDS = ("grammar", "vocabulary", "pronunciation", "fluency", "structures", "overall")


class SpeakingGradingService:
    def __init__(self, db, llm, speech, storage):
        self.db, self.llm = db, llm
        self.processor = SpeechTranscriptionService(db, speech, storage)

    async def grade(self, session_id: str, user_id: str, answer_id: str | None = None):
        session = await owned_speaking_session(self.db, session_id, user_id)
        if session.status == "IN_PROGRESS" and (session.mode == "FULL_TEST" or not answer_id):
            raise AppError(409, "Hãy hoàn thành bài nói trước khi chấm.", "exam_feedback_locked")
        if answer_id:
            answer = await owned_speaking_answer(self.db, answer_id, user_id)
            if answer.session_id != session_id:
                raise AppError(404, "Không tìm thấy câu trả lời.")
            answers = [answer]
        else:
            answers = list(session.answers)
        if not any(a.audio_path for a in answers):
            raise AppError(
                422, "Phiên chưa có bản ghi để chấm. Hãy bắt đầu một lượt luyện mới.", "audio_required"
            )
        for answer in answers:
            if answer.audio_path:
                await self.processor.transcribe(answer, user_id)
                await self.processor.analyze(answer, user_id)
        target = answer_id or session_id
        await speech_lock(self.db, f"speaking-grade:{user_id}:{target}")
        # Prevent a practice retake from racing with this immutable grading snapshot.
        session = await owned_speaking_session(self.db, session_id, user_id, lock=True)
        answers = [a for a in session.answers if not answer_id or a.id == answer_id]
        source = [
            {
                "sequence_number": a.sequence_number,
                "part": a.part,
                "question": session.question_set[a.sequence_number],
                "transcript": a.transcript or "",
                "audio_hash": a.audio_hash,
                "status": a.status,
                "metrics": a.metrics,
                "audio_analysis": a.audio_analysis
                or {"available": False, "evidence": "", "reason_vi": "Câu hỏi chưa có bản ghi."},
            }
            for a in answers
        ]
        if any(a.audio_path and a.transcript is None for a in answers):
            raise AppError(409, "Bản ghi đã thay đổi trong lúc xử lý. Hãy thử lại.", "audio_changed")
        part = 0 if session.mode == "FULL_TEST" and not answer_id else answers[0].part
        payload = {
            "part": part,
            "mode": session.mode if not answer_id else f"PART{part}",
            "confidence_threshold": settings.pronunciation_confidence_threshold,
            "answers": source,
        }
        # Session UUIDs never enter the cache; the ordered prompts/audio/transcripts do.
        cache_payload = copy.deepcopy(payload)
        for entry in cache_payload["answers"]:
            entry["question"].pop("question_id", None)
        key = speech_cache_key(
            json.dumps(cache_payload, sort_keys=True, ensure_ascii=False),
            settings.openai_model,
            settings.openai_transcribe_model,
            settings.openai_speaking_audio_model,
            SPEAKING_GRADER_PROMPT_VERSION,
        )
        await speech_lock(self.db, f"speaking-cache:{user_id}:{key}")
        query = (
            select(SpeakingGrading).where(SpeakingGrading.answer_id == answer_id)
            if answer_id
            else select(SpeakingGrading).where(SpeakingGrading.session_id == session_id)
        )
        existing = await self.db.scalar(query)
        if existing and existing.cache_key == key:
            await self.db.commit()
            await sync_learning(user_id, "SPEAKING", session_id)
            return existing
        cached = await self.db.scalar(
            select(SpeakingGrading)
            .where(SpeakingGrading.user_id == user_id, SpeakingGrading.cache_key == key)
            .limit(1)
        )
        if cached:
            values = {
                name: copy.deepcopy(getattr(cached, name))
                for name in (
                    *FEEDBACK_FIELDS,
                    "estimated_level",
                    "audio_coverage",
                    "ai_model",
                    "audio_model",
                    "transcription_model",
                    "prompt_version",
                )
            }
            values.update({f"{key}_score": getattr(cached, f"{key}_score") for key in SCORE_FIELDS})
            errors = [
                {
                    key: getattr(e, key)
                    for key in (
                        "sequence_number",
                        "category",
                        "subtype",
                        "original",
                        "corrected",
                        "explanation_vi",
                        "severity",
                        "confidence",
                    )
                }
                for e in cached.errors
            ]
        else:
            text_payload = {
                "part": part,
                "mode": payload["mode"],
                "answers": [
                    {key: a[key] for key in ("sequence_number", "part", "question", "transcript", "status")}
                    for a in source
                ],
            }
            text_result = await self.llm.grade_speaking(text_payload, user_id)
            result, coverage = SpeakingCorrectionService().finalize(text_result, source)
            data = result.model_dump()
            values = {name: data[name] for name in FEEDBACK_FIELDS}
            values.update({f"{key}_score": value for key, value in data["scores"].items()})
            values.update(
                estimated_level=speaking_level(result.scores.overall),
                audio_coverage=coverage,
                ai_model=settings.openai_model,
                audio_model=settings.openai_speaking_audio_model or None,
                transcription_model=settings.openai_transcribe_model,
                prompt_version=SPEAKING_GRADER_PROMPT_VERSION,
            )
            errors = data["grammar_errors"] + data["other_errors"]
        grading = existing or SpeakingGrading(
            user_id=user_id, session_id=None if answer_id else session_id, answer_id=answer_id
        )
        for name, value in values.items():
            setattr(grading, name, value)
        grading.cache_key = key
        grading.errors = [SpeakingError(**error) for error in errors]
        self.db.add(grading)
        if not answer_id:
            session.status = "GRADED"
        await self.db.commit()
        await sync_learning(user_id, "SPEAKING", session_id)
        return grading
