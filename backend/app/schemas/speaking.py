from typing import Literal

from pydantic import Field, model_validator

from app.common.test_profiles import TestProfile
from app.schemas.writing import Improvement, StrictModel

SpeakingMode = Literal["FULL_TEST", "PART1", "PART2", "PART3", "QUICK_PRACTICE"]
SPEAKING_TOPICS = [
    "education",
    "family",
    "travel",
    "shopping",
    "health",
    "work",
    "technology",
    "leisure",
    "community",
    "transportation",
    "environment",
    "social_activities",
    "books",
    "sports",
    "holidays",
    "study",
    "career",
    "food",
    "films",
    "hometown",
    "friends",
    "music",
    "daily_life",
]


class SpeakingQuestionRequest(StrictModel):
    part: Literal[1, 2, 3]
    topic: str = "random"
    test_profile: TestProfile = "VSTEP_3_5"
    source: Literal["AI", "SEED", "BANK"] = "BANK"
    recent_question_ids: list[str] = Field(default_factory=list, max_length=45)
    recent_topics: list[str] = Field(default_factory=list, max_length=15)

    @model_validator(mode="after")
    def valid_topic(self):
        if self.topic != "random" and self.topic not in SPEAKING_TOPICS:
            raise ValueError("Chủ đề Speaking không hợp lệ")
        return self


class TopicSet(StrictModel):
    topic: str
    questions: list[str] = Field(min_length=1, max_length=3)


class GeneratedSpeakingQuestion(StrictModel):
    part: Literal[1, 2, 3]
    question_type: Literal["social_interaction", "solution_discussion", "topic_development"]
    topic: str
    question_text: str = Field(min_length=15, max_length=3000)
    topic_sets: list[TopicSet]
    situation: str | None
    options: list[str]
    suggested_ideas: list[str]
    allow_own_idea: bool
    follow_up_questions: list[str]
    test_profile: TestProfile = "VSTEP_3_5"

    @model_validator(mode="after")
    def validate_format(self):
        if (
            self.question_type
            != {1: "social_interaction", 2: "solution_discussion", 3: "topic_development"}[self.part]
        ):
            raise ValueError("Invalid VSTEP Speaking type")
        if self.topic not in SPEAKING_TOPICS:
            raise ValueError("Invalid topic")
        if self.part == 1:
            if len(self.topic_sets) != 2 or not 3 <= sum(len(t.questions) for t in self.topic_sets) <= 6:
                raise ValueError("Part 1 requires two topics and 3–6 questions")
            if self.topic_sets[0].topic.lower() == self.topic_sets[1].topic.lower():
                raise ValueError("Part 1 topics must differ")
        if self.part == 2 and (
            not self.situation
            or len(self.options) != 3
            or len(set(self.options)) != 3
            or any(not option.strip() for option in self.options)
        ):
            raise ValueError("Part 2 requires a situation and three distinct options")
        if self.part == 3 and (
            len(self.suggested_ideas) != 3
            or not self.allow_own_idea
            or not 2 <= len(self.follow_up_questions) <= 3
        ):
            raise ValueError("Part 3 requires three ideas, own idea and 2–3 follow-ups")
        return self


class SpeakingSessionCreate(StrictModel):
    mode: SpeakingMode
    source: Literal["AI", "SEED", "BANK"] = "BANK"
    topic: str = "random"
    test_profile: TestProfile = "VSTEP_3_5"
    question_id: str | None = None

    @model_validator(mode="after")
    def valid_topic(self):
        if self.topic != "random" and self.topic not in SPEAKING_TOPICS:
            raise ValueError("Chủ đề Speaking không hợp lệ")
        return self


class SpeakingAnswerCreate(StrictModel):
    sequence_number: int = Field(ge=0, le=120)


class SpeakingAdvance(SpeakingAnswerCreate):
    skip: bool = False


class TranscriptionResult(StrictModel):
    text: str
    model: str
    segments: list[dict] = Field(default_factory=list)


class SpeakingScores(StrictModel):
    grammar: float = Field(ge=0, le=10)
    vocabulary: float = Field(ge=0, le=10)
    pronunciation: float | None = Field(ge=0, le=10)
    fluency: float | None = Field(ge=0, le=10)
    structures: float = Field(ge=0, le=10)
    overall: float | None = Field(ge=0, le=10)


class SpeakingErrorOutput(StrictModel):
    sequence_number: int
    category: Literal[
        "grammar", "vocabulary", "pronunciation", "fluency", "coherence", "content", "task_response"
    ]
    subtype: str
    original: str
    corrected: str
    explanation_vi: str
    severity: Literal["minor", "major", "critical"]
    confidence: float | None = Field(ge=0, le=1)


class PronunciationItem(StrictModel):
    sequence_number: int
    word: str
    issue: Literal[
        "individual_sound", "word_stress", "sentence_stress", "final_sound", "intonation", "clarity"
    ]
    feedback_vi: str
    ipa: str | None
    suggestion: str
    confidence: float = Field(ge=0, le=1)


class SpeakingVocabulary(StrictModel):
    sequence_number: int
    original: str
    suggestion: str
    reason_vi: str
    example: str


class SpokenCorrection(StrictModel):
    sequence_number: int
    original: str
    corrected: str
    explanation_vi: str
    start_seconds: float | None = Field(ge=0)


class AnswerFeedback(StrictModel):
    sequence_number: int
    part: Literal[1, 2, 3]
    summary_vi: str
    best_option_clearly_stated: bool | None
    reasons_developed_vi: str
    other_options_discussed_vi: str
    corrected_transcript: str
    improved_b2_answer: str


class SpeakingGradingOutput(StrictModel):
    part: Literal[0, 1, 2, 3]
    scores: SpeakingScores
    pronunciation_confidence: float = Field(ge=0, le=1)
    fluency_confidence: float = Field(ge=0, le=1)
    summary_vi: str
    strengths: list[str]
    priority_improvements: list[Improvement] = Field(min_length=3, max_length=3)
    grammar_errors: list[SpeakingErrorOutput]
    other_errors: list[SpeakingErrorOutput]
    vocabulary_suggestions: list[SpeakingVocabulary]
    pronunciation_feedback: list[PronunciationItem]
    fluency_feedback: list[Improvement]
    structure_feedback: list[Improvement]
    content_feedback: list[Improvement]
    sentence_corrections: list[SpokenCorrection]
    answer_feedback: list[AnswerFeedback]
    speaking_frame: list[Improvement]
    corrected_transcript: str
    improved_b2_answer: str


class SpeakingTextScores(StrictModel):
    grammar: float = Field(ge=0, le=10, multiple_of=0.5)
    vocabulary: float = Field(ge=0, le=10, multiple_of=0.5)
    structures: float = Field(ge=0, le=10, multiple_of=0.5)


class SpeakingTextGradingOutput(StrictModel):
    part: Literal[0, 1, 2, 3]
    scores: SpeakingTextScores
    confidence: float = Field(default=0.8, ge=0, le=1)
    summary_vi: str
    strengths: list[str]
    priority_improvements: list[Improvement] = Field(min_length=3, max_length=3)
    grammar_errors: list[SpeakingErrorOutput]
    other_errors: list[SpeakingErrorOutput]
    vocabulary_suggestions: list[SpeakingVocabulary]
    structure_feedback: list[Improvement]
    content_feedback: list[Improvement]
    sentence_corrections: list[SpokenCorrection]
    answer_feedback: list[AnswerFeedback]
    speaking_frame: list[Improvement]
    corrected_transcript: str
    improved_b2_answer: str

    @model_validator(mode="after")
    def language_only(self):
        if any(e.category in {"pronunciation", "fluency"} for e in self.grammar_errors + self.other_errors):
            raise ValueError("Acoustic diagnostics belong to the audio provider only")
        return self
