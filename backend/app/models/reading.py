from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdentityMixin, UpdatedMixin, utcnow


class ReadingPassage(IdentityMixin, Base):
    __tablename__ = "reading_passages"
    title: Mapped[str] = mapped_column(String(300))
    topic: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[str] = mapped_column(String(5), index=True)
    content: Mapped[str] = mapped_column(Text)
    paragraphs: Mapped[list] = mapped_column(JSONB)
    word_count: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), default="SEED")
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    prompt_version: Mapped[str | None] = mapped_column(String(30))
    vocabulary_cache: Mapped[dict] = mapped_column(JSONB, default=dict)
    questions: Mapped[list["ReadingQuestion"]] = relationship(
        lazy="selectin", order_by="ReadingQuestion.question_number", cascade="all, delete-orphan"
    )


class ReadingQuestion(IdentityMixin, Base):
    __tablename__ = "reading_questions"
    __table_args__ = (
        UniqueConstraint("passage_id", "question_number"),
        CheckConstraint("correct_answer IN ('A','B','C','D')"),
    )
    passage_id: Mapped[str] = mapped_column(ForeignKey("reading_passages.id", ondelete="CASCADE"), index=True)
    question_number: Mapped[int] = mapped_column(Integer)
    question_type: Mapped[str] = mapped_column(String(40), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSONB)
    correct_answer: Mapped[str] = mapped_column(String(1))
    explanation_vi: Mapped[str] = mapped_column(Text)
    option_explanations: Mapped[dict] = mapped_column(JSONB)
    evidence: Mapped[dict] = mapped_column(JSONB)
    difficulty: Mapped[str] = mapped_column(String(5))


class ReadingExamSession(IdentityMixin, Base):
    __tablename__ = "reading_exam_sessions"
    __table_args__ = (
        CheckConstraint("mode IN ('FULL_TEST','PASSAGE_PRACTICE','QUICK_PRACTICE','QUESTION_TYPE_PRACTICE')"),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(30))
    difficulty: Mapped[str] = mapped_column(String(5))
    topic: Mapped[str] = mapped_column(String(40), default="random")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS", index=True)
    question_count: Mapped[int] = mapped_column(Integer)
    passage_ids: Mapped[list] = mapped_column(JSONB)
    question_ids: Mapped[list] = mapped_column(JSONB)
    answers: Mapped[list["ReadingAnswer"]] = relationship(lazy="selectin", cascade="all, delete-orphan")
    result: Mapped["ReadingResult | None"] = relationship(
        lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )


class ReadingAnswer(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "reading_answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id"),
        CheckConstraint("selected_answer IS NULL OR selected_answer IN ('A','B','C','D')"),
        CheckConstraint("time_spent_seconds >= 0"),
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("reading_exam_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[str] = mapped_column(ForeignKey("reading_questions.id"))
    selected_answer: Mapped[str | None] = mapped_column(String(1))
    is_marked_for_review: Mapped[bool] = mapped_column(Boolean, default=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    first_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[ReadingQuestion] = relationship(lazy="selectin")


class ReadingResult(IdentityMixin, Base):
    __tablename__ = "reading_results"
    session_id: Mapped[str] = mapped_column(
        ForeignKey("reading_exam_sessions.id", ondelete="CASCADE"), unique=True
    )
    correct_count: Mapped[int] = mapped_column(Integer)
    incorrect_count: Mapped[int] = mapped_column(Integer)
    unanswered_count: Mapped[int] = mapped_column(Integer)
    accuracy: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    question_type_breakdown: Mapped[list] = mapped_column(JSONB)
    passage_breakdown: Mapped[list] = mapped_column(JSONB)
    strategy_feedback: Mapped[list] = mapped_column(JSONB)
