from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.speaking import AudioAnalysisResult, TranscriptionResult


class SpeechClient(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: Path, user_id: str) -> TranscriptionResult: ...

    @abstractmethod
    async def analyze_audio(self, audio_path: Path, transcript: str, user_id: str) -> AudioAnalysisResult: ...

    @abstractmethod
    async def synthesize(self, text: str, user_id: str) -> bytes: ...
