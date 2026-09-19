from typing import Literal

from pydantic import Field

from app.schemas.writing import Improvement, StrictModel
from app.schemas.writing_assessment import WritingAnalysis


class SourceEvidence(StrictModel):
    sentence_id: int | None = Field(ge=1)
    explanation_vi: str = Field(min_length=10, max_length=300)


class SourceCriterion(StrictModel):
    positive_evidence: list[SourceEvidence] = Field(max_length=2)
    negative_evidence: list[SourceEvidence] = Field(max_length=2)
    assessment_vi: str = Field(max_length=400)


class SourceCriteria(StrictModel):
    task_fulfillment: SourceCriterion
    organization: SourceCriterion
    vocabulary: SourceCriterion
    grammar: SourceCriterion


class SourceCoverage(StrictModel):
    requirement: str
    coverage: Literal["missing", "mentioned", "developed", "well_developed"]
    evidence: list[SourceEvidence] = Field(max_length=2)


class CoreAnalysis(WritingAnalysis):
    criteria: SourceCriteria
    task_coverage: list[SourceCoverage] = Field(min_length=1)


class CoreCriterion(StrictModel):
    score: float = Field(ge=0, le=10, multiple_of=0.5)
    justification_vi: str = Field(min_length=30, max_length=500)


class CoreScores(StrictModel):
    task_fulfillment: CoreCriterion
    organization: CoreCriterion
    vocabulary: CoreCriterion
    grammar: CoreCriterion


class WritingCoreOutput(StrictModel):
    analysis: CoreAnalysis
    scores: CoreScores
    confidence: float = Field(ge=0, le=1)
    uncertainties: list[str] = Field(max_length=3)
    summary_vi: str = Field(min_length=15, max_length=600)
    top_improvements: list[Improvement] = Field(min_length=3, max_length=3)
