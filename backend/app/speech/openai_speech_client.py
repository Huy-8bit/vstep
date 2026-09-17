import base64
import logging
import time
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from starlette.concurrency import run_in_threadpool

from app.common.errors import AppError
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AIUsageLog
from app.prompts.speaking_grader import SPEAKING_AUDIO_PROMPT
from app.schemas.speaking import AudioAnalysisResult, TranscriptionResult
from app.speech.base import SpeechClient

logger = logging.getLogger(__name__)


class OpenAISpeechClient(SpeechClient):
    async def _call(self, operation, model, user_id, callback):
        if not settings.openai_api_key:
            raise AppError(503, "Chưa cấu hình OpenAI API. Bản ghi của bạn đã được lưu.", "ai_not_configured")
        start, result, status = time.monotonic(), None, "error"
        try:
            async with AsyncOpenAI(api_key=settings.openai_api_key, timeout=150, max_retries=0) as client:
                result = await callback(client)
                status = "success"
                return result
        except APITimeoutError:
            status = "timeout"
            raise AppError(
                504, "AI xử lý audio quá lâu. Bản ghi đã được lưu, bạn có thể thử lại.", "speech_timeout"
            ) from None
        except APIConnectionError:
            raise AppError(
                502, "Không kết nối được dịch vụ giọng nói. Bản ghi vẫn được giữ.", "speech_unavailable"
            ) from None
        except APIStatusError as exc:
            status = f"http_{exc.status_code}"
            raise AppError(
                502,
                "Dịch vụ giọng nói chưa xử lý được yêu cầu. Kiểm tra model, quyền truy cập và hạn mức OpenAI.",
                "speech_unavailable",
            ) from None
        finally:
            try:
                usage = getattr(result, "usage", None)
                async with SessionLocal() as db:
                    db.add(
                        AIUsageLog(
                            user_id=user_id,
                            operation=operation,
                            model=model,
                            input_tokens=getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0))
                            or 0,
                            output_tokens=getattr(
                                usage, "output_tokens", getattr(usage, "completion_tokens", 0)
                            )
                            or 0,
                            latency_ms=int((time.monotonic() - start) * 1000),
                            status=status,
                        )
                    )
                    await db.commit()
            except Exception:
                logger.error("Could not persist speech usage metadata")

    async def transcribe(self, audio_path: Path, user_id: str) -> TranscriptionResult:
        async def send(client):
            with audio_path.open("rb") as audio:
                return await client.audio.transcriptions.create(
                    model=settings.openai_transcribe_model, file=audio, language="en", response_format="json"
                )

        result = await self._call("speaking_transcribe", settings.openai_transcribe_model, user_id, send)
        if not isinstance(result.text, str):
            raise AppError(502, "Không nhận được bản chuyển lời nói hợp lệ.", "transcript_invalid")
        return TranscriptionResult(text=result.text.strip(), model=settings.openai_transcribe_model)

    async def analyze_audio(self, audio_path: Path, transcript: str, user_id: str) -> AudioAnalysisResult:
        model = settings.openai_speaking_audio_model
        if not model:
            return AudioAnalysisResult(
                available=False,
                evidence="",
                model=None,
                reason_vi="Chưa cấu hình model phân tích audio; phát âm và độ trôi chảy chưa được chấm.",
            )
        encoded = base64.b64encode(await run_in_threadpool(audio_path.read_bytes)).decode("ascii")

        async def send(client):
            return await client.chat.completions.create(
                model=model,
                modalities=["text"],
                store=False,
                messages=[
                    {"role": "system", "content": SPEAKING_AUDIO_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Reference transcript (may contain recognition errors; judge the AUDIO):\n"
                                + transcript,
                            },
                            {"type": "input_audio", "input_audio": {"data": encoded, "format": "wav"}},
                        ],
                    },
                ],
            )

        result = await self._call("speaking_audio", model, user_id, send)
        evidence = result.choices[0].message.content if result.choices else None
        if not evidence:
            raise AppError(502, "AI chưa trả được phân tích audio.", "audio_analysis_invalid")
        # Audio models need not support JSON Schema. Their actual audio-grounded evidence feeds
        # the configured text model's strictly validated final grading, never invented phonetics.
        return AudioAnalysisResult(available=True, evidence=evidence[:24000], model=model, reason_vi=None)

    async def synthesize(self, text: str, user_id: str) -> bytes:
        async def send(client):
            return await client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
                response_format="mp3",
            )

        result = await self._call("speaking_tts", settings.openai_tts_model, user_id, send)
        return result.content
