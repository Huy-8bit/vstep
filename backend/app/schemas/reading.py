from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from app.common.test_profiles import ItemDifficultyBand, TestProfile
from app.common.words import count_words
from app.schemas.writing import StrictModel

ReadingMode = Literal["FULL_TEST", "PASSAGE_PRACTICE", "QUICK_PRACTICE", "QUESTION_TYPE_PRACTICE"]
ReadingType = Literal[
    "main_idea",
    "detail",
    "inference",
    "vocabulary",
    "reference",
    "purpose",
    "negative_detail",
    "sentence_meaning",
    "organization",
    "tone",
    "attitude",
    "sentence_insertion",
    "paragraph_completion",
]
Option = Literal["A", "B", "C", "D"]
READING_TOPICS = [
    "education",
    "technology",
    "environment",
    "health",
    "science",
    "society",
    "culture",
    "work",
    "business",
    "travel",
    "psychology",
    "history",
    "communication",
    "nature",
    "lifestyle",
]
READING_TYPES = [
    "main_idea",
    "detail",
    "inference",
    "vocabulary",
    "reference",
    "purpose",
    "negative_detail",
    "sentence_meaning",
    "organization",
    "tone",
    "attitude",
    "sentence_insertion",
    "paragraph_completion",
]


class Paragraph(StrictModel):
    id: str = Field(pattern=r"^p[1-9][0-9]*$")
    text: str = Field(min_length=40, max_length=4000)


class Options(StrictModel):
    A: str = Field(min_length=1, max_length=700)
    B: str = Field(min_length=1, max_length=700)
    C: str = Field(min_length=1, max_length=700)
    D: str = Field(min_length=1, max_length=700)


class OptionExplanation(StrictModel):
    is_correct: bool
    explanation_vi: str = Field(min_length=10, max_length=1500)


class OptionExplanations(StrictModel):
    A: OptionExplanation
    B: OptionExplanation
    C: OptionExplanation
    D: OptionExplanation


class Evidence(StrictModel):
    paragraph_id: str
    quote: str = Field(min_length=5, max_length=1800)


class InsertionPosition(StrictModel):
    label: Option
    after_text: str = Field(min_length=5, max_length=600)


class ReadingPlacement(StrictModel):
    paragraph_id: str
    sentence_to_insert: str | None
    positions: list[InsertionPosition]


class GeneratedReadingQuestion(StrictModel):
    internal_difficulty_band: ItemDifficultyBand
    question_number: int = Field(ge=1, le=10)
    question_type: ReadingType
    question_text: str = Field(min_length=10, max_length=1200)
    options: Options
    correct_answer: Option
    explanation_vi: str = Field(min_length=10, max_length=2000)
    option_explanations: OptionExplanations
    evidence: Evidence
    placement: ReadingPlacement | None = None


class GeneratedReadingPassage(StrictModel):
    title: str = Field(min_length=5, max_length=300)
    topic: str
    test_profile: TestProfile = "VSTEP_3_5"
    internal_difficulty_band: ItemDifficultyBand
    paragraphs: list[Paragraph] = Field(min_length=3, max_length=8)
    questions: list[GeneratedReadingQuestion] = Field(min_length=5, max_length=10)

    @model_validator(mode="after")
    def consistent(self):
        if self.topic not in READING_TOPICS:
            raise ValueError("Unknown reading topic")
        if [p.id for p in self.paragraphs] != [f"p{i + 1}" for i in range(len(self.paragraphs))]:
            raise ValueError("Paragraph ids must be sequential")
        words = count_words("\n\n".join(p.text for p in self.paragraphs))
        lower = 220 if len(self.questions) == 5 else 430
        if not lower <= words <= 650:
            raise ValueError(f"Passage requires {lower}–650 words, received {words}")
        if sorted(q.question_number for q in self.questions) != list(range(1, len(self.questions) + 1)):
            raise ValueError("Question numbers must be unique and sequential")
        if len({q.question_text.strip().casefold() for q in self.questions}) != len(self.questions):
            raise ValueError("Duplicate questions")
        paragraphs = {p.id: p.text for p in self.paragraphs}
        for q in self.questions:
            if (
                q.evidence.paragraph_id not in paragraphs
                or q.evidence.quote not in paragraphs[q.evidence.paragraph_id]
            ):
                raise ValueError("Evidence must quote an exact substring in its paragraph")
            if q.question_type == "sentence_insertion":
                placement = q.placement
                if (
                    not placement
                    or not placement.sentence_to_insert
                    or placement.paragraph_id not in paragraphs
                ):
                    raise ValueError("Insertion requires a sentence and a known paragraph")
                if [p.label for p in placement.positions] != list("ABCD"):
                    raise ValueError("Insertion needs four labelled positions")
                paragraph = paragraphs[placement.paragraph_id]
                ends = [paragraph.find(p.after_text) + len(p.after_text) for p in placement.positions]
                if any(
                    p.after_text not in paragraph or paragraph.count(p.after_text) != 1
                    for p in placement.positions
                ) or ends != sorted(set(ends)):
                    raise ValueError("Insertion positions must be unique ordered exact text anchors")
            elif q.placement is not None:
                raise ValueError("Placement metadata belongs only to sentence insertion items")
            options = q.options.model_dump()
            if len({v.strip().casefold() for v in options.values()}) != 4:
                raise ValueError("Options must differ")
            for letter, explanation in q.option_explanations.model_dump().items():
                if explanation["is_correct"] != (letter == q.correct_answer):
                    raise ValueError("Exactly one correct explanation must match the answer key")
        if len({q.internal_difficulty_band for q in self.questions}) < 2:
            raise ValueError("A passage must include variation in item demands")
        distribution = Counter(q.correct_answer for q in self.questions)
        if len(distribution) < 3 or max(distribution.values()) > (len(self.questions) + 1) // 2:
            raise ValueError("Answer distribution is too predictable")
        return self


class ReadingGenerateRequest(StrictModel):
    mode: ReadingMode = "PASSAGE_PRACTICE"
    test_profile: TestProfile = "VSTEP_3_5"
    topic: str = "random"
    question_count: Literal[5, 10] = 10
    target_question_types: list[ReadingType] = Field(default_factory=list, max_length=10)
    recent_topics: list[str] = Field(default_factory=list, max_length=20)
    recent_titles: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def topic_valid(self):
        if self.mode == "FULL_TEST" and (self.question_count != 10 or self.target_question_types):
            raise ValueError("Full-test passages follow the internal 4-passage/40-question blueprint")
        if self.topic != "random" and self.topic not in READING_TOPICS:
            raise ValueError("Invalid topic")
        return self


class ReadingSessionCreate(StrictModel):
    mode: ReadingMode = "FULL_TEST"
    test_profile: TestProfile = "VSTEP_3_5"
    topic: str = "random"
    target_question_type: ReadingType | None = None
    timed: bool = False
    passage_id: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.topic != "random" and self.topic not in READING_TOPICS:
            raise ValueError("Invalid topic")
        if self.mode == "QUESTION_TYPE_PRACTICE" and not self.target_question_type:
            raise ValueError("Question type is required")
        if self.mode == "FULL_TEST" and self.passage_id:
            raise ValueError("Full test selects four passages from the bank")
        return self


class ReadingAnswerUpdate(StrictModel):
    selected_answer: Option | None
    is_marked_for_review: bool = False
    revision: int = Field(ge=0)
    time_spent_seconds: int = Field(default=0, ge=0, le=86400)


class ReadingBatchUpdate(StrictModel):
    answers: dict[str, ReadingAnswerUpdate] = Field(default_factory=dict, max_length=40)


class VocabularyRequest(StrictModel):
    session_id: str
    passage_id: str
    paragraph_id: str
    term: str = Field(min_length=1, max_length=100)


class ReadingVocabulary(StrictModel):
    term: str
    meaning_vi: str
    part_of_speech: str
    meaning_in_context: str
    example: str
    synonyms: list[str]
