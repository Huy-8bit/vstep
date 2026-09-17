from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin, UpdatedMixin


class VocabularyRecommendationBatch(IdentityMixin, Base):
    __tablename__ = "vocabulary_recommendation_batches"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_skill: Mapped[str] = mapped_column(String(20))
    source_attempt_id: Mapped[str] = mapped_column(String(36))
    source_topic: Mapped[str] = mapped_column(String(50))
    cache_key: Mapped[str] = mapped_column(String(64))
    items: Mapped[list] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(30))
    __table_args__ = (UniqueConstraint("user_id", "cache_key"),)


class UserVocabularyItem(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "user_vocabulary_items"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    headword: Mapped[str] = mapped_column(String(150))
    phrase: Mapped[str] = mapped_column(String(250))
    part_of_speech: Mapped[str] = mapped_column(String(100))
    meaning_vi: Mapped[str] = mapped_column(Text)
    meaning_in_context_vi: Mapped[str] = mapped_column(Text)
    register: Mapped[str] = mapped_column(String(40))
    collocations: Mapped[list] = mapped_column(JSONB)
    common_patterns: Mapped[list] = mapped_column(JSONB)
    source_skill: Mapped[str] = mapped_column(String(20))
    source_attempt_id: Mapped[str] = mapped_column(String(36))
    source_topic: Mapped[str] = mapped_column(String(50), index=True)
    user_original_text: Mapped[str | None] = mapped_column(Text)
    improved_text: Mapped[str | None] = mapped_column(Text)
    example_sentence: Mapped[str] = mapped_column(Text)
    why_learn_this_vi: Mapped[str] = mapped_column(Text)
    issue_type: Mapped[str] = mapped_column(String(40))
    priority: Mapped[str] = mapped_column(String(10))
    exercise_data: Mapped[dict] = mapped_column(JSONB)
    mastery_level: Mapped[str] = mapped_column(String(20), default="NEW", index=True)
    mastery_step: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = (UniqueConstraint("user_id", "fingerprint"),)


class VocabularyItemSource(IdentityMixin, Base):
    __tablename__ = "vocabulary_item_sources"
    item_id: Mapped[str] = mapped_column(
        ForeignKey("user_vocabulary_items.id", ondelete="CASCADE"), index=True
    )
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("vocabulary_recommendation_batches.id", ondelete="CASCADE")
    )
    item_index: Mapped[int] = mapped_column(Integer)
    source_skill: Mapped[str] = mapped_column(String(20))
    source_attempt_id: Mapped[str] = mapped_column(String(36))
    source_topic: Mapped[str] = mapped_column(String(50))
    __table_args__ = (UniqueConstraint("batch_id", "item_index"),)


class VocabularyReview(IdentityMixin, Base):
    __tablename__ = "vocabulary_reviews"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str] = mapped_column(
        ForeignKey("user_vocabulary_items.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    prompt: Mapped[dict] = mapped_column(JSONB)
    expected: Mapped[dict] = mapped_column(JSONB)
    answer: Mapped[str | None] = mapped_column(Text)
    correct: Mapped[bool | None] = mapped_column(Boolean)
    feedback: Mapped[dict | None] = mapped_column(JSONB)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assessment_model: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[float | None] = mapped_column(Float)
    client_request_id: Mapped[str] = mapped_column(String(36))
    __table_args__ = (UniqueConstraint("user_id", "client_request_id"),)
