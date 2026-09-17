from pydantic import Field

from app.schemas.writing import StrictModel


class ReadingItemQuality(StrictModel):
    question_number: int
    single_best_answer: bool
    supported_by_evidence: bool
    plausible_distractors: bool
    independently_selected_answer: str
    confidence: float = Field(ge=0, le=1)
    notes: str


class QuestionQualityReview(StrictModel):
    accepted: bool
    confidence: float = Field(ge=0, le=1)
    realistic_context: bool
    no_specialist_knowledge: bool
    no_embedded_answer: bool
    requirements_consistent: bool
    notes: list[str]
    reading_items: list[ReadingItemQuality]
