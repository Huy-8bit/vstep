from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.speaking import TranscriptionResult


class SpeechClient(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: Path, user_id: str) -> TranscriptionResult: ...

    @abstractmethod
    async def synthesize(self, text: str, user_id: str) -> bytes: ...
