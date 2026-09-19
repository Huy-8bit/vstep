from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.writing import StrictModel

LearningSkill = Literal["WRITING", "SPEAKING", "READING", "CROSS"]
ExerciseKind = Literal[
    "MULTIPLE_CHOICE",
    "FILL_BLANK",
    "ERROR_CORRECTION",
    "SENTENCE_TRANSFORMATION",
    "COLLOCATION",
    "NATURAL_EXPRESSION",
    "REWRITE_SENTENCE",
    "CONTEXTUAL_GAP",
    "ACTIVE_RECALL",
    "FIX_SENTENCE",
    "IMPROVE_PARAGRAPH",
    "WRITE_INTRODUCTION",
    "DEVELOP_IDEA",
    "MINI_TASK1",
    "MINI_TASK2",
    "READING_TARGETED",
    "SHORT_ANSWER",
    "SENTENCE_EXPANSION",
    "TIMED_RESPONSE",
    "PRONUNCIATION_WORDS",
    "REUSE_VOCABULARY",
    "PART2_COMPARISON",
    "PART3_DEVELOPMENT",
]


class LessonExample(StrictModel):
    english: str
    explanation_vi: str


class UserLessonExample(StrictModel):
    signal_id: str
    original: str
    corrected: str | None
    explanation_vi: str


class PersonalizedLessonOutput(StrictModel):
    title: str = Field(min_length=3, max_length=200)
    why_this_matters_vi: str = Field(max_length=1500)
    simple_explanation_vi: str = Field(max_length=3000)
    rules: list[str] = Field(min_length=1, max_length=6)
    examples: list[LessonExample] = Field(min_length=2, max_length=5)
    examples_from_user_errors: list[UserLessonExample] = Field(max_length=5)
    common_traps: list[str] = Field(min_length=1, max_length=5)
    quick_check: list[str] = Field(min_length=1, max_length=4)
    practice_recommendation: str


class ExerciseItem(StrictModel):
    kind: ExerciseKind
    instruction_vi: str = Field(min_length=5, max_length=1000)
    text: str = Field(min_length=3, max_length=5000)
    options: list[str] = Field(max_length=4)
    accepted_answers: list[str] = Field(max_length=10)
    sample_answer: str = Field(max_length=4000)
    explanation_vi: str = Field(min_length=10, max_length=2000)
    rubric: list[str] = Field(min_length=1, max_length=5)
    passage: str | None = Field(max_length=8000)
    target_words: list[str] = Field(max_length=12)
    seconds: int | None = Field(ge=15, le=300)
    evaluation: Literal["OBJECTIVE", "COACH", "RECORDING"]

    @model_validator(mode="after")
    def valid_key(self):
        if self.evaluation == "OBJECTIVE" and not self.accepted_answers:
            raise ValueError("Objective exercise needs an answer key")
        if self.options and (len(self.options) < 2 or len(set(self.options)) != len(self.options)):
            raise ValueError("Distinct choices required")
        if self.options and any(a not in self.options for a in self.accepted_answers):
            raise ValueError("Answer must use an exact option string")
        if self.kind == "READING_TARGETED" and not self.passage:
            raise ValueError("Reading needs its passage")
        speaking = {
            "SHORT_ANSWER",
            "SENTENCE_EXPANSION",
            "TIMED_RESPONSE",
            "PRONUNCIATION_WORDS",
            "REUSE_VOCABULARY",
            "PART2_COMPARISON",
            "PART3_DEVELOPMENT",
        }
        if self.kind in speaking and self.evaluation != "RECORDING":
            raise ValueError("Spoken drills must use the existing audio practice engine")
        return self


class PersonalizedExercisesOutput(StrictModel):
    title: str
    concept_key: str
    items: list[ExerciseItem] = Field(min_length=5, max_length=10)


class ExerciseAssessment(StrictModel):
    concept_correct: bool | None
    confidence: float = Field(ge=0, le=1)
    explanation_vi: str = Field(min_length=10, max_length=1500)
    suggested_answer: str = Field(max_length=4000)
    evidence_quote: str = Field(max_length=4000)


class PracticeCreate(StrictModel):
    client_request_id: UUID
    kind: ExerciseKind | None = None
    count: Literal[5, 8, 10] = 8
    second_chance: bool = False


class ExerciseSubmit(StrictModel):
    item_index: int = Field(ge=0, le=9)
    answer: str = Field(min_length=1, max_length=6000)
    duration_seconds: int = Field(default=0, ge=0, le=900)


class PlanCreate(StrictModel):
    duration_days: Literal[7, 14, 30] = 7
    daily_minutes: Literal[15, 25, 40] = 25


class PlanItemUpdate(StrictModel):
    status: Literal["PENDING", "COMPLETED", "SKIPPED"]


class TargetPracticeCreate(StrictModel):
    client_request_id: UUID
    skill: Literal["WRITING", "SPEAKING", "READING"]
    source: Literal["BANK", "AI"] = "AI"
    part: Literal[1, 2, 3] | None = None
    exercise_id: str | None = None
    item_index: int | None = Field(default=None, ge=0, le=9)

    @model_validator(mode="after")
    def valid_source(self):
        if self.source == "BANK" and self.skill != "READING":
            raise ValueError("Bank selection is available for targeted Reading only")
        return self


class WeeklyRecommendation(StrictModel):
    weakness_id: str
    reason_vi: str = Field(min_length=10, max_length=500)
    activity_vi: str = Field(min_length=10, max_length=500)


class WeeklyCoachOutput(StrictModel):
    summary_vi: str = Field(min_length=10, max_length=1200)
    recommendations: list[WeeklyRecommendation] = Field(max_length=3)
