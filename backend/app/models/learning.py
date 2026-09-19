"""Versioned evidence, small structured aggregates and private learning artifacts."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin, UpdatedMixin


class UserLearningProfile(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "user_learning_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    analysis_version: Mapped[str] = mapped_column(String(30))
    backfill_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    backfill_processed: Mapped[int] = mapped_column(Integer, default=0)
    backfill_error: Mapped[str | None] = mapped_column(String(80))


class LearningAttempt(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "learning_attempts"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    attempt_id: Mapped[str] = mapped_column(String(36))
    skill: Mapped[str] = mapped_column(String(20))
    source_version: Mapped[str] = mapped_column(String(64))
    analysis_version: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exposure: Mapped[int] = mapped_column(Integer)
    scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    lexical_counts: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_url: Mapped[str] = mapped_column(String(150))
    __table_args__ = (
        UniqueConstraint("user_id", "skill", "attempt_id"),
        Index("ix_learning_attempt_user_skill_time", "user_id", "skill", "occurred_at"),
    )


class LearningSignal(IdentityMixin, Base):
    __tablename__ = "learning_signals"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    attempt_id: Mapped[str] = mapped_column(String(36))
    skill: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30))
    subcategory: Mapped[str] = mapped_column(String(80))
    concept_key: Mapped[str] = mapped_column(String(100))
    original_text: Mapped[str | None] = mapped_column(Text)
    corrected_text: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    outcome: Mapped[str] = mapped_column(String(20), default="ERROR")
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    fingerprint: Mapped[str] = mapped_column(String(64))
    source_version: Mapped[str] = mapped_column(String(64))
    grader_version: Mapped[str] = mapped_column(String(80))
    analysis_version: Mapped[str] = mapped_column(String(30))
    taxonomy_version: Mapped[str] = mapped_column(String(30))
    model: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        UniqueConstraint("user_id", "skill", "attempt_id", "source_version", "fingerprint"),
        Index("ix_learning_signal_user_concept_time", "user_id", "concept_key", "active", "created_at"),
        Index("ix_learning_signal_user_skill_attempt", "user_id", "skill", "attempt_id"),
    )


class UserWeakness(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "user_weaknesses"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    skill: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30))
    subcategory: Mapped[str] = mapped_column(String(80))
    concept_key: Mapped[str] = mapped_column(String(100))
    display_name_vi: Mapped[str] = mapped_column(String(250))
    display_name_en: Mapped[str] = mapped_column(String(250))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    affected_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    recent_occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="NEW")
    mastery_status: Mapped[str] = mapped_column(String(20), default="NOT_STARTED")
    trend: Mapped[str] = mapped_column(String(25), default="INSUFFICIENT_DATA")
    priority_score: Mapped[float] = mapped_column(Float, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("user_id", "skill", "concept_key"),
        Index("ix_weakness_user_priority", "user_id", "priority_score"),
    )


class UserLearningEvent(IdentityMixin, Base):
    __tablename__ = "user_learning_events"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    skill: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(30))
    concept_key: Mapped[str] = mapped_column(String(100))
    source_attempt_id: Mapped[str | None] = mapped_column(String(36))
    source_exercise_id: Mapped[str | None] = mapped_column(String(36))
    dedup_key: Mapped[str] = mapped_column(String(160))
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("user_id", "dedup_key"),
        Index("ix_learning_event_user_concept_time", "user_id", "concept_key", "created_at"),
    )


class LearningLesson(IdentityMixin, Base):
    __tablename__ = "learning_lessons"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    weakness_id: Mapped[str] = mapped_column(ForeignKey("user_weaknesses.id", ondelete="CASCADE"))
    concept_key: Mapped[str] = mapped_column(String(100))
    skill: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[str] = mapped_column(String(30))
    cache_key: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("user_id", "cache_key"),)


class PersonalizedExercise(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "personalized_exercises"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    weakness_id: Mapped[str] = mapped_column(ForeignKey("user_weaknesses.id", ondelete="CASCADE"))
    concept_key: Mapped[str] = mapped_column(String(100))
    skill: Mapped[str] = mapped_column(String(20))
    exercise_type: Mapped[str] = mapped_column(String(40))
    content: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    client_request_id: Mapped[str] = mapped_column(String(36))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("user_id", "client_request_id"),)


class LearningExerciseAnswer(IdentityMixin, Base):
    __tablename__ = "learning_exercise_answers"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[str] = mapped_column(ForeignKey("personalized_exercises.id", ondelete="CASCADE"))
    item_index: Mapped[int] = mapped_column(Integer)
    answer: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool | None] = mapped_column(Boolean)
    feedback: Mapped[dict] = mapped_column(JSONB)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("exercise_id", "item_index"),
        Index("ix_learning_answer_user_time", "user_id", "created_at"),
    )


class StudyPlan(IdentityMixin, Base):
    __tablename__ = "study_plans"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    duration_days: Mapped[int] = mapped_column(Integer)
    daily_minutes: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    profile_revision: Mapped[int] = mapped_column(Integer)


class StudyPlanItem(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "study_plan_items"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_id: Mapped[str] = mapped_column(ForeignKey("study_plans.id", ondelete="CASCADE"))
    weakness_id: Mapped[str | None] = mapped_column(ForeignKey("user_weaknesses.id", ondelete="SET NULL"))
    date: Mapped[date] = mapped_column(Date)
    skill: Mapped[str] = mapped_column(String(20))
    concept_key: Mapped[str] = mapped_column(String(100))
    activity_type: Mapped[str] = mapped_column(String(30))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    details: Mapped[dict] = mapped_column("metadata", JSONB)
    __table_args__ = (Index("ix_study_item_user_date", "user_id", "date"),)
