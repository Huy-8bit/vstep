import asyncio
import hashlib
from pathlib import Path

from app.common.errors import AppError
from app.core.config import settings


class TextToSpeechService:
    def __init__(self, speech):
        self.speech = speech

    async def speak_question(self, text: str, user_id: str) -> Path:
        if not settings.openai_tts_model:
            raise AppError(409, "Dùng giọng đọc có sẵn của trình duyệt.", "browser_tts")
        text = text[:3500]
        key = hashlib.sha256(
            f"{settings.openai_tts_model}:{settings.openai_tts_voice}:{text}".encode()
        ).hexdigest()
        folder = Path(settings.audio_storage_dir) / "tts"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{key}.mp3"
        if not path.exists():
            content = await self.speech.synthesize(text, user_id)
            await asyncio.to_thread(path.write_bytes, content)
        return path
