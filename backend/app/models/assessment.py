from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin, UpdatedMixin


class WritingGradingRevision(IdentityMixin, Base):
    __tablename__ = "writing_grading_revisions"
    attempt_id: Mapped[str] = mapped_column(ForeignKey("writing_attempts.id", ondelete="CASCADE"), index=True)
    grader_version: Mapped[str] = mapped_column(String(30))
    grading_model: Mapped[str] = mapped_column(String(100))
    snapshot: Mapped[dict] = mapped_column(JSONB)


class WritingCalibrationSample(IdentityMixin, Base):
    __tablename__ = "writing_calibration_samples"
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    human_task_score: Mapped[float | None] = mapped_column(Float)
    human_organization_score: Mapped[float | None] = mapped_column(Float)
    human_vocabulary_score: Mapped[float | None] = mapped_column(Float)
    human_grammar_score: Mapped[float | None] = mapped_column(Float)
    human_overall_score: Mapped[float | None] = mapped_column(Float)
    reviewer_count: Mapped[int] = mapped_column(Integer, default=0)


class PronunciationPractice(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "pronunciation_practices"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reference_text: Mapped[str] = mapped_column(String(500))
    reference_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_answer_id: Mapped[str | None] = mapped_column(
        ForeignKey("speaking_answers.id", ondelete="SET NULL")
    )
    source_issue_type: Mapped[str | None] = mapped_column(String(40))
    audio_path: Mapped[str | None] = mapped_column(Text)
    audio_hash: Mapped[str | None] = mapped_column(String(64))
    audio_duration_ms: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="CREATED")
    analysis: Mapped[dict | None] = mapped_column(JSONB)
    analysis_key: Mapped[str | None] = mapped_column(String(64), index=True)
    pronunciation_score: Mapped[float | None] = mapped_column(Float)
    fluency_score: Mapped[float | None] = mapped_column(Float)
    audio_model: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(30))
    client_request_id: Mapped[str] = mapped_column(String(36))
    __table_args__ = (UniqueConstraint("user_id", "client_request_id"),)
