from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdentityMixin, UpdatedMixin, utcnow
from app.models.library import LibrarySessionMixin, PrivateQuestionMixin
from app.models.speaking import (  # noqa: F401
    SpeakingAnswer,
    SpeakingError,
    SpeakingExamSession,
    SpeakingGrading,
    SpeakingQuestion,
)


class User(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class AuthSession(IdentityMixin, Base):
    __tablename__ = "auth_sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WritingQuestion(PrivateQuestionMixin, IdentityMixin, Base):
    __tablename__ = "writing_questions"
    __table_args__ = (
        CheckConstraint("task_type IN (1, 2)"),
        CheckConstraint("minimum_words > 0"),
    )
    task_type: Mapped[int] = mapped_column(Integer, index=True)
    question_type: Mapped[str] = mapped_column(String(50))
    topic: Mapped[str] = mapped_column(String(50), index=True)
    # Retained only to preserve historical data; never used for generation or public DTOs.
    legacy_difficulty: Mapped[str | None] = mapped_column("difficulty", String(10))
    test_profile: Mapped[str] = mapped_column(String(20), default="VSTEP_3_5", server_default="VSTEP_3_5")
    instruction: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list] = mapped_column(JSONB, default=list)
    minimum_words: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(10), default="SEED")
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    generation_diagnostics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    stimulus: Mapped[str | None] = mapped_column(Text)
    response_instruction: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(20))
    register: Mapped[str | None] = mapped_column(String(20))
    recipient_relationship: Mapped[str | None] = mapped_column(String(50))
    purpose: Mapped[str | None] = mapped_column(Text)


class ExamSession(LibrarySessionMixin, IdentityMixin, Base):
    __tablename__ = "exam_sessions"
    __table_args__ = (CheckConstraint("mode IN ('FULL_TEST', 'TASK1', 'TASK2')"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_profile: Mapped[str] = mapped_column(String(20), default="VSTEP_3_5", server_default="VSTEP_3_5")
    mode: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")
    attempts: Mapped[list["WritingAttempt"]] = relationship(
        back_populates="exam", lazy="selectin", order_by="WritingAttempt.task_type"
    )


class WritingAttempt(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "writing_attempts"
    __table_args__ = (UniqueConstraint("exam_session_id", "task_type"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("writing_questions.id"))
    exam_session_id: Mapped[str] = mapped_column(
        ForeignKey("exam_sessions.id", ondelete="CASCADE"), index=True
    )
    task_type: Mapped[int] = mapped_column(Integer)
    answer: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    question: Mapped[WritingQuestion] = relationship(lazy="selectin")
    exam: Mapped[ExamSession] = relationship(back_populates="attempts")
    grading_work: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    grading: Mapped["WritingGrading | None"] = relationship(
        back_populates="attempt", lazy="selectin", uselist=False
    )


class WritingGrading(IdentityMixin, Base):
    __tablename__ = "writing_gradings"
    __table_args__ = tuple(
        CheckConstraint(f"{s}_score >= 0 AND {s}_score <= 10")
        for s in (
            "task_fulfillment",
            "organization",
            "vocabulary",
            "grammar",
            "overall",
        )
    )
    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("writing_attempts.id", ondelete="CASCADE"), unique=True
    )
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    task_fulfillment_score: Mapped[float] = mapped_column(Float)
    organization_score: Mapped[float] = mapped_column(Float)
    vocabulary_score: Mapped[float] = mapped_column(Float)
    grammar_score: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    summary_vi: Mapped[str] = mapped_column(Text)
    strengths: Mapped[list] = mapped_column(JSONB)
    priority_improvements: Mapped[list] = mapped_column(JSONB)
    structure_feedback: Mapped[list] = mapped_column(JSONB)
    task_fulfillment_feedback: Mapped[list] = mapped_column(JSONB)
    vocabulary_suggestions: Mapped[list] = mapped_column(JSONB)
    sentence_feedback: Mapped[list] = mapped_column(JSONB)
    corrected_version: Mapped[str] = mapped_column(Text)
    improved_b2_version: Mapped[str] = mapped_column(Text)
    ai_model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(20))
    grader_version: Mapped[str] = mapped_column(String(30), default="2.0.0", server_default="1.0.0")
    analysis_prompt_version: Mapped[str | None] = mapped_column(String(30))
    calibration_prompt_version: Mapped[str | None] = mapped_column(String(30))
    criterion_evidence: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    analysis_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    attempt: Mapped[WritingAttempt] = relationship(back_populates="grading")
    errors: Mapped[list["WritingError"]] = relationship(lazy="selectin", cascade="all, delete-orphan")


class WritingError(IdentityMixin, Base):
    __tablename__ = "writing_errors"
    grading_id: Mapped[str] = mapped_column(ForeignKey("writing_gradings.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    subtype: Mapped[str] = mapped_column(String(80))
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    explanation_vi: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))


class AIUsageLog(IdentityMixin, Base):
    __tablename__ = "ai_usage_logs"
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    operation: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    reasoning_effort: Mapped[str | None] = mapped_column(String(20))
    cached_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(14, 8))
    attempt_id: Mapped[str | None] = mapped_column(String(36))
    category: Mapped[str] = mapped_column(String(30), default="legacy")
    evaluation_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        Index("ix_ai_usage_time_category", "created_at", "category"),
        Index("ix_ai_usage_user_attempt", "user_id", "attempt_id"),
    )


from app.models.assessment import (  # noqa: F401, E402
    PronunciationPractice,
    WritingCalibrationSample,
    WritingGradingRevision,
)
from app.models.evaluation import GradingModelEvaluation  # noqa: E402,F401
from app.models.learning import (  # noqa: E402,F401
    LearningAttempt,
    LearningExerciseAnswer,
    LearningLesson,
    LearningSignal,
    PersonalizedExercise,
    StudyPlan,
    StudyPlanItem,
    UserLearningEvent,
    UserLearningProfile,
    UserWeakness,
)
from app.models.library import (  # noqa: E402,F401
    LibraryQuestion,
    LibraryRevision,
    QuestionCollection,
    QuestionImportFile,
)
from app.models.reading import (  # noqa: F401, E402
    ReadingAnswer,
    ReadingExamSession,
    ReadingPassage,
    ReadingQuestion,
    ReadingResult,
)
from app.models.vocabulary import (  # noqa: F401, E402
    UserVocabularyItem,
    VocabularyItemSource,
    VocabularyRecommendationBatch,
    VocabularyReview,
)
