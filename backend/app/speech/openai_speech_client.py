import logging
import time
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.common.errors import AppError
from app.core.config import settings
from app.llm.usage import record_usage
from app.schemas.speaking import TranscriptionResult
from app.speech.base import SpeechClient

logger = logging.getLogger(__name__)


class OpenAISpeechClient(SpeechClient):
    async def call(self, operation, model, user_id, callback):
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
            await record_usage(
                user_id=user_id,
                operation=operation,
                model=getattr(result, "model", None) or model,
                reasoning_effort=None,
                usage=getattr(result, "usage", None),
                latency_ms=int((time.monotonic() - start) * 1000),
                status=status,
                category="transcription" if operation == "speaking_transcribe" else "audio",
                response_id=getattr(result, "id", None),
            )

    async def transcribe(self, audio_path: Path, user_id: str) -> TranscriptionResult:
        async def send(client):
            with audio_path.open("rb") as audio:
                return await client.audio.transcriptions.create(
                    model=settings.openai_transcribe_model, file=audio, language="en", response_format="json"
                )

        result = await self.call("speaking_transcribe", settings.openai_transcribe_model, user_id, send)
        if not isinstance(result.text, str):
            raise AppError(502, "Không nhận được bản chuyển lời nói hợp lệ.", "transcript_invalid")
        return TranscriptionResult(text=result.text.strip(), model=settings.openai_transcribe_model)

    async def synthesize(self, text: str, user_id: str) -> bytes:
        async def send(client):
            return await client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
                response_format="mp3",
            )

        result = await self.call("speaking_tts", settings.openai_tts_model, user_id, send)
        return result.content
