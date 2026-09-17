from abc import ABC, abstractmethod

from app.schemas.reading import GeneratedReadingPassage, ReadingVocabulary
from app.schemas.speaking import GeneratedSpeakingQuestion, SpeakingTextGradingOutput
from app.schemas.writing import GeneratedQuestion, ImprovedWriting
from app.schemas.writing_assessment import WritingAnalysis, WritingCalibration, WritingFeedback


class LLMClient(ABC):
    @abstractmethod
    async def generate_question(self, payload: dict, user_id: str) -> GeneratedQuestion: ...

    @abstractmethod
    async def analyze_writing(self, payload: dict, user_id: str) -> WritingAnalysis: ...

    @abstractmethod
    async def calibrate_writing(self, payload: dict, user_id: str) -> WritingCalibration: ...

    @abstractmethod
    async def writing_feedback(self, payload: dict, user_id: str) -> WritingFeedback: ...

    @abstractmethod
    async def improve_writing(self, payload: dict, user_id: str) -> ImprovedWriting: ...

    @abstractmethod
    async def generate_speaking_question(self, payload: dict, user_id: str) -> GeneratedSpeakingQuestion: ...

    @abstractmethod
    async def grade_speaking(self, payload: dict, user_id: str) -> SpeakingTextGradingOutput: ...

    @abstractmethod
    async def generate_reading(self, payload: dict, user_id: str) -> GeneratedReadingPassage: ...

    @abstractmethod
    async def explain_reading_vocabulary(self, payload: dict, user_id: str) -> ReadingVocabulary: ...
