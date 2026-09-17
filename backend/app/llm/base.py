from abc import ABC, abstractmethod

from app.schemas.speaking import GeneratedSpeakingQuestion, SpeakingGradingOutput
from app.schemas.writing import GeneratedQuestion, GradingOutput, ImprovedWriting


class LLMClient(ABC):
    @abstractmethod
    async def generate_question(self, payload: dict, user_id: str) -> GeneratedQuestion: ...

    @abstractmethod
    async def grade_writing(self, payload: dict, user_id: str) -> GradingOutput: ...

    @abstractmethod
    async def improve_writing(self, payload: dict, user_id: str) -> ImprovedWriting: ...

    @abstractmethod
    async def generate_speaking_question(self, payload: dict, user_id: str) -> GeneratedSpeakingQuestion: ...

    @abstractmethod
    async def grade_speaking(self, payload: dict, user_id: str) -> SpeakingGradingOutput: ...
