import asyncio
import hashlib
import os
from pathlib import Path
from uuid import uuid4

from app.common.errors import AppError
from app.core.config import settings
from app.services.speech_transcription_service import speech_lock


class TextToSpeechService:
    def __init__(self, speech, db):
        self.speech, self.db = speech, db

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
        await speech_lock(self.db, f"tts:{key}")
        if not path.exists():
            content = await self.speech.synthesize(text, user_id)
            temporary = folder / f"{uuid4().hex}.tmp"
            try:
                await asyncio.to_thread(temporary.write_bytes, content)
                await asyncio.to_thread(os.replace, temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        await self.db.commit()
        return path
