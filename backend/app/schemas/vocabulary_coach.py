from typing import Literal

from pydantic import Field, model_validator

from app.schemas.writing import StrictModel

VocabularySourceSkill = Literal["WRITING", "SPEAKING", "READING"]
ReviewKind = Literal["RECALL", "GAP", "COLLOCATION", "CORRECT", "USE"]


class VocabularyLearningItem(StrictModel):
    headword: str = Field(min_length=1, max_length=150)
    phrase: str = Field(min_length=1, max_length=250)
    part_of_speech: str = Field(min_length=1, max_length=100)
    meaning_vi: str = Field(min_length=5, max_length=1500)
    meaning_in_context_vi: str = Field(min_length=5, max_length=1500)
    register: Literal["informal", "neutral", "formal"] = Field(...)
    collocations: list[str] = Field(min_length=1, max_length=6)
    common_patterns: list[str] = Field(min_length=1, max_length=6)
    user_original: str = Field(max_length=1200)
    better_version: str = Field(max_length=1500)
    example_sentence: str = Field(min_length=10, max_length=1000)
    why_learn_this_vi: str = Field(min_length=10, max_length=1500)
    source_type: Literal[
        "UNNATURAL_EXPRESSION", "TOPIC", "REPEATED_ERROR", "SPOKEN_EXPRESSION", "READING_CONTEXT"
    ]
    issue_type: Literal[
        "word_choice", "collocation", "word_form", "countability", "register", "lexical_gap", "word_family"
    ]
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    natural_options: list[str] = Field(min_length=1, max_length=4)
    collocation_distractors: list[str] = Field(min_length=3, max_length=3)
    accepted_phrases: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def exercises_valid(self):
        if self.phrase.casefold() not in self.example_sentence.casefold():
            raise ValueError("Example must contain the exact phrase to support contextual gap practice")
        options = [self.phrase, *self.collocation_distractors]
        if len(set(s.strip().casefold() for s in options)) != 4:
            raise ValueError("Collocation options must differ")
        if not any(self.phrase.casefold() == s.casefold() for s in self.accepted_phrases):
            raise ValueError("Recall answer must include the target phrase")
        return self


class VocabularyCoachOutput(StrictModel):
    items: list[VocabularyLearningItem] = Field(min_length=1, max_length=16)


class VocabularyRecommendationRequest(StrictModel):
    source_skill: VocabularySourceSkill
    source_attempt_id: str
    passage_id: str | None = None
    paragraph_id: str | None = None
    term: str | None = Field(default=None, min_length=1, max_length=100)


class VocabularySave(StrictModel):
    batch_id: str
    item_index: int = Field(ge=0, le=15)


class VocabularyReviewCreate(StrictModel):
    kind: ReviewKind
    client_request_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")


class VocabularyReviewAnswer(StrictModel):
    answer: str = Field(min_length=1, max_length=1200)


class VocabularyUsageAssessment(StrictModel):
    correct: bool
    confidence: float = Field(ge=0, le=1)
    explanation_vi: str = Field(min_length=10, max_length=1500)
    corrected_sentence: str = Field(max_length=1500)
