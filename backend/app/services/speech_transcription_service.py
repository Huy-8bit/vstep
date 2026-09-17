import hashlib
import re

from sqlalchemy import select, text

from app.common.errors import AppError
from app.common.words import count_words
from app.core.config import settings
from app.models.speaking import SpeakingAnswer, SpeakingExamSession
from app.prompts.speaking_grader import SPEAKING_AUDIO_PROMPT_VERSION
from app.schemas.speaking import AudioAnalysisResult


def speech_cache_key(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


async def speech_lock(db, key: str):
    lock_id = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], signed=True)
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})


class SpeechTranscriptionService:
    def __init__(self, db, speech, storage):
        self.db, self.speech, self.storage = db, speech, storage

    async def _lock_recording(self, answer, user_id):
        # Retakes and processing share a session row lock; never attach an old transcript
        # to a new recording while a practice upload is in flight.
        await self.db.execute(
            select(SpeakingExamSession.id)
            .where(SpeakingExamSession.id == answer.session_id, SpeakingExamSession.user_id == user_id)
            .with_for_update()
        )
        await self.db.refresh(answer)

    async def transcribe(self, answer: SpeakingAnswer, user_id: str):
        await self._lock_recording(answer, user_id)
        if not answer.audio_path or not answer.audio_hash:
            raise AppError(409, "Câu trả lời chưa có bản ghi.", "audio_required")
        key = speech_cache_key(answer.audio_hash, settings.openai_transcribe_model)
        await speech_lock(self.db, f"transcribe:{user_id}:{key}")
        await self.db.refresh(answer)
        if answer.transcription_key == key and answer.transcript is not None:
            await self.db.commit()
            return answer
        cached = await self.db.scalar(
            select(SpeakingAnswer)
            .join(SpeakingExamSession)
            .where(
                SpeakingExamSession.user_id == user_id,
                SpeakingAnswer.transcription_key == key,
                SpeakingAnswer.transcript.is_not(None),
            )
            .limit(1)
        )
        if cached:
            transcript = cached.transcript
        elif answer.metrics.get("peak_rms_estimate", 1) < 0.0001:
            transcript = ""  # Do not ask STT to hallucinate speech over an empty recording.
        else:
            result = await self.speech.transcribe(self.storage.resolve(answer.audio_path), user_id)
            transcript = result.text
        answer.transcript, answer.transcription_key = transcript, key
        answer.transcription_model = settings.openai_transcribe_model
        answer.transcript_hash = speech_cache_key(transcript)
        answer.word_count = count_words(transcript)
        tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", transcript.lower())
        duration = (answer.audio_duration_ms or 0) / 1000
        answer.metrics = {
            **answer.metrics,
            "total_words": answer.word_count,
            "words_per_minute": round(answer.word_count / duration * 60, 1) if duration else None,
            "filler_count": sum(t in {"uh", "um", "erm"} for t in tokens),
            "filler_candidate_count": len(
                re.findall(r"\b(?:you know|i mean|well|actually|like)\b", transcript, re.I)
            ),
            "repetition_count": sum(a == b for a, b in zip(tokens, tokens[1:])),
            "transcript_note_vi": "Từ đệm và lặp từ được đếm trên bản chuyển lời nói, có thể thiếu hoặc sai do nhận dạng giọng nói.",
        }
        answer.status = "TRANSCRIBED"
        await self.db.commit()
        return answer

    async def analyze(self, answer: SpeakingAnswer, user_id: str, retry: bool = False):
        if answer.transcript is None:
            answer = await self.transcribe(answer, user_id)
        await self._lock_recording(answer, user_id)
        if not answer.audio_hash or answer.transcript is None:
            raise AppError(409, "Bản ghi đã thay đổi. Hãy xử lý lại.", "audio_changed")
        key = speech_cache_key(
            answer.audio_hash,
            answer.transcript_hash,
            settings.openai_speaking_audio_model,
            SPEAKING_AUDIO_PROMPT_VERSION,
        )
        await speech_lock(self.db, f"audio-analysis:{user_id}:{key}")
        await self.db.refresh(answer)
        if (
            answer.audio_analysis_key == key
            and answer.audio_analysis
            and (answer.audio_analysis.get("available") or not retry)
        ):
            await self.db.commit()
            return answer
        cached = await self.db.scalar(
            select(SpeakingAnswer)
            .join(SpeakingExamSession)
            .where(
                SpeakingExamSession.user_id == user_id,
                SpeakingAnswer.audio_analysis_key == key,
                SpeakingAnswer.id != answer.id,
            )
            .limit(1)
        )
        if cached and cached.audio_analysis and cached.audio_analysis.get("available"):
            answer.audio_analysis = cached.audio_analysis
        else:
            try:
                result = await self.speech.analyze_audio(
                    self.storage.resolve(answer.audio_path), answer.transcript or "", user_id
                )
            except AppError as exc:
                # Preserve transcript feedback if the optional acoustic model is unavailable.
                result = AudioAnalysisResult(
                    available=False,
                    evidence="",
                    model=settings.openai_speaking_audio_model or None,
                    reason_vi=exc.message,
                )
            answer.audio_analysis = result.model_dump()
        answer.audio_analysis_key = key
        await self.db.commit()
        return answer
