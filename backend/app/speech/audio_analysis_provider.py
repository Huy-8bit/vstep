from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.audio_assessment import AudioAssessment


class AudioAnalysisProvider(ABC):
    @abstractmethod
    async def assess(self, audio_path: Path, context: dict, user_id: str) -> AudioAssessment: ...
