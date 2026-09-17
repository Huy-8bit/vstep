from typing import Literal

from pydantic import Field, model_validator

from app.schemas.writing import StrictModel

AUDIO_SCORE_FIELDS = (
    "pronunciation_score",
    "intelligibility_score",
    "clarity_score",
    "stress_score",
    "intonation_score",
    "rhythm_score",
    "fluency_score",
)


class AudioIssue(StrictModel):
    type: Literal[
        "word_pronunciation",
        "final_sound",
        "word_stress",
        "sentence_stress",
        "intonation",
        "rhythm",
        "hesitation",
        "clarity",
    ]
    target: str = Field(min_length=1, max_length=500)
    description_vi: str = Field(min_length=10, max_length=1500)
    suggestion_vi: str = Field(min_length=10, max_length=1500)
    confidence: float = Field(ge=0, le=1)
    audible_evidence_vi: str = Field(min_length=10, max_length=1500)


class AudioAssessment(StrictModel):
    available: bool
    speech_present: bool
    reason_vi: str | None
    confidence: float = Field(ge=0, le=1)
    pronunciation_confidence: float = Field(ge=0, le=1)
    fluency_confidence: float = Field(ge=0, le=1)
    pronunciation_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    intelligibility_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    clarity_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    stress_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    intonation_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    rhythm_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    fluency_score: float | None = Field(ge=0, le=10, multiple_of=0.5)
    pronunciation_summary_vi: str
    fluency_summary_vi: str
    issues: list[AudioIssue] = Field(max_length=20)
    heard_text: str
    reference_coverage: float | None = Field(ge=0, le=1)
    stress_feedback_vi: str
    issue_vi: str
    practice_tip_vi: str

    @model_validator(mode="after")
    def available_scores(self):
        if not self.available or not self.speech_present:
            self.available = False
            for field in AUDIO_SCORE_FIELDS:
                setattr(self, field, None)
            self.issues = []
        return self


def unavailable_audio(reason):
    return AudioAssessment(
        available=False,
        speech_present=False,
        reason_vi=reason,
        confidence=0,
        pronunciation_confidence=0,
        fluency_confidence=0,
        **{field: None for field in AUDIO_SCORE_FIELDS},
        pronunciation_summary_vi="",
        fluency_summary_vi="",
        issues=[],
        heard_text="",
        reference_coverage=None,
        stress_feedback_vi="",
        issue_vi="",
        practice_tip_vi="",
    )


class PronunciationCreate(StrictModel):
    reference_text: str = Field(min_length=1, max_length=500)
    source_answer_id: str | None = None
    source_issue_type: str | None = Field(default=None, max_length=40)
    client_request_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")
