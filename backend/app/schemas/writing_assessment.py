from typing import Literal

from pydantic import Field, model_validator

from app.schemas.writing import (
    ErrorFeedback,
    Improvement,
    SentenceFeedback,
    StrictModel,
    VocabularySuggestion,
)
from app.vstep_reference.scoring_reference import WRITING_CRITERIA

CRITERIA = WRITING_CRITERIA


class WritingEvidence(StrictModel):
    quote: str
    explanation_vi: str = Field(min_length=10)


class CriterionEvidence(StrictModel):
    positive_evidence: list[WritingEvidence]
    negative_evidence: list[WritingEvidence]
    assessment_vi: str


class AnalysisCriteria(StrictModel):
    task_fulfillment: CriterionEvidence
    organization: CriterionEvidence
    vocabulary: CriterionEvidence
    grammar: CriterionEvidence


class TaskCoverage(StrictModel):
    requirement: str
    coverage: Literal["missing", "mentioned", "developed", "well_developed"]
    evidence: list[WritingEvidence]


class AnalyzedSentence(StrictModel):
    sentence_id: int = Field(ge=1)
    structure: Literal["simple", "compound", "complex", "compound_complex", "fragment"]
    relative_clauses: int = Field(ge=0, le=10)
    conditionals: int = Field(ge=0, le=10)
    subordination: int = Field(ge=0, le=10)
    control: Literal["controlled", "partly_controlled", "uncontrolled"]


class DetectedWritingError(ErrorFeedback):
    sentence_id: int = Field(ge=1)
    primary_criterion: Literal["grammar", "vocabulary", "organization", "task_fulfillment"]


class WritingAnalysis(StrictModel):
    task: Literal[1, 2]
    task_coverage: list[TaskCoverage] = Field(min_length=1)
    idea_development: Literal["absent", "basic", "adequate", "strong"]
    cohesion: Literal["limited", "basic", "effective", "sophisticated"]
    lexical_range: Literal["very_limited", "basic", "varied", "precise_flexible"]
    criteria: AnalysisCriteria
    sentences: list[AnalyzedSentence]
    errors: list[DetectedWritingError]
    relevance_vi: str
    register_vi: str


class CalibratedCriterion(CriterionEvidence):
    initial_score: float = Field(ge=0, le=10, multiple_of=0.5)
    score: float = Field(ge=0, le=10, multiple_of=0.5)
    score_justification_vi: str = Field(min_length=30)
    consistency_review_vi: str = Field(min_length=30)
    high_score_justification_vi: str

    @model_validator(mode="after")
    def justified_high_score(self):
        if self.score >= 7 and (
            len(self.high_score_justification_vi.strip()) < 80
            or len({item.quote for item in self.positive_evidence if item.quote.strip()}) < 2
        ):
            raise ValueError("A score of 7+ needs specific positive evidence and a substantive justification")
        return self


class WritingCalibration(StrictModel):
    task_fulfillment: CalibratedCriterion
    organization: CalibratedCriterion
    vocabulary: CalibratedCriterion
    grammar: CalibratedCriterion
    calibration_summary_vi: str


class WritingFeedback(StrictModel):
    summary_vi: str
    strengths: list[str]
    priority_improvements: list[Improvement] = Field(min_length=3, max_length=3)
    structure_feedback: list[Improvement]
    task_fulfillment_feedback: list[Improvement]
    vocabulary_suggestions: list[VocabularySuggestion]


class WritingCorrections(StrictModel):
    sentence_feedback: list[SentenceFeedback]
    corrected_version: str
    improved_b2_version: str
