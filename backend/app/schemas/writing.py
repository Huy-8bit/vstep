from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.common.test_profiles import TestProfile

TASK1_TYPES = [
    "formal_email",
    "informal_email",
    "request",
    "complaint",
    "apology",
    "invitation",
    "giving_information",
    "asking_for_information",
    "thank_you_letter",
    "giving_advice",
]
TASK2_TYPES = [
    "opinion",
    "agree_disagree",
    "discussion",
    "advantages_disadvantages",
    "problems_solutions",
    "causes_solutions",
    "causes_effects",
    "two_part_question",
]
TOPICS = [
    "education",
    "technology",
    "environment",
    "work",
    "health",
    "transport",
    "family",
    "social_media",
    "tourism",
    "culture",
    "city_life",
    "crime",
    "community",
    "leisure",
    "public_services",
    "shopping",
    "sports",
    "young_people",
    "older_people",
    "migration",
    "communication",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionRequest(StrictModel):
    task: Literal[1, 2]
    question_type: str = "random"
    topic: str = "random"
    test_profile: TestProfile = "VSTEP_3_5"
    source: Literal["AI", "SEED", "BANK"] = "BANK"
    exclude_ids: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def valid_options(self):
        if self.question_type != "random" and self.question_type not in (
            TASK1_TYPES if self.task == 1 else TASK2_TYPES
        ):
            raise ValueError("Dạng đề không phù hợp với task.")
        if self.topic != "random" and self.topic not in TOPICS:
            raise ValueError("Chủ đề không hợp lệ.")
        return self


class GeneratedQuestion(StrictModel):
    task: Literal[1, 2]
    question_type: str
    topic: str
    test_profile: TestProfile = "VSTEP_3_5"
    instruction: str = Field(min_length=30, max_length=5000)
    stimulus: str = Field(min_length=100, max_length=1800)
    response_instruction: str = Field(min_length=20, max_length=1200)
    genre: Literal["email", "letter", "essay"]
    register: Literal["informal", "semi-formal", "formal"] = Field(...)
    recipient_relationship: str = Field(max_length=50)
    purpose: str = Field(max_length=1000)
    requirements: list[str] = Field(
        validation_alias=AliasChoices("communicative_requirements", "requirements")
    )
    minimum_words: Literal[120, 250]

    @model_validator(mode="after")
    def vstep_format(self):
        allowed = TASK1_TYPES if self.task == 1 else TASK2_TYPES
        if self.question_type not in allowed or self.topic not in TOPICS:
            raise ValueError("Invalid VSTEP question metadata")
        if self.minimum_words != (120 if self.task == 1 else 250):
            raise ValueError("Invalid minimum words")
        if self.task == 1 and not 2 <= len(self.requirements) <= 4:
            raise ValueError("Task 1 must include two to four requirements")
        return self


class Scores(StrictModel):
    task_fulfillment: float = Field(ge=0, le=10)
    organization: float = Field(ge=0, le=10)
    vocabulary: float = Field(ge=0, le=10)
    grammar: float = Field(ge=0, le=10)
    overall: float = Field(ge=0, le=10)


class Improvement(StrictModel):
    title_vi: str
    explanation_vi: str
    example: str


class ErrorFeedback(StrictModel):
    category: Literal[
        "grammar",
        "vocabulary",
        "spelling",
        "punctuation",
        "collocation",
        "word_choice",
        "sentence_structure",
        "cohesion",
        "task_response",
        "register",
    ]
    subtype: str
    original: str
    corrected: str
    explanation_vi: str
    severity: Literal["minor", "major", "critical"]


class VocabularySuggestion(StrictModel):
    original: str
    suggestion: str
    reason_vi: str
    example: str


class SentenceFeedback(StrictModel):
    original: str
    corrected: str
    explanation_vi: str


class GradingOutput(StrictModel):
    task: Literal[1, 2]
    word_count: int = Field(ge=0)
    scores: Scores
    summary_vi: str
    strengths: list[str]
    priority_improvements: list[Improvement] = Field(min_length=3, max_length=3)
    structure_feedback: list[Improvement]
    task_fulfillment_feedback: list[Improvement]
    errors: list[ErrorFeedback]
    vocabulary_suggestions: list[VocabularySuggestion]
    sentence_feedback: list[SentenceFeedback]
    corrected_version: str
    improved_b2_version: str


class ImprovedWriting(StrictModel):
    corrected_version: str
    improved_b2_version: str
