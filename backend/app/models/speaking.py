from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdentityMixin, UpdatedMixin, utcnow
from app.models.library import LibrarySessionMixin, PrivateQuestionMixin


class SpeakingQuestion(PrivateQuestionMixin, IdentityMixin, Base):
    __tablename__ = "speaking_questions"
    __table_args__ = (CheckConstraint("part IN (1, 2, 3)"),)
    part: Mapped[int] = mapped_column(Integer, index=True)
    question_type: Mapped[str] = mapped_column(String(40))
    topic: Mapped[str] = mapped_column(String(80), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    topic_sets: Mapped[list] = mapped_column(JSONB, default=list)
    situation: Mapped[str | None] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSONB, default=list)
    suggested_ideas: Mapped[list] = mapped_column(JSONB, default=list)
    follow_up_questions: Mapped[list] = mapped_column(JSONB, default=list)
    # Retained only to preserve historical data; never used for generation or public DTOs.
    legacy_difficulty: Mapped[str | None] = mapped_column("difficulty", String(10))
    test_profile: Mapped[str] = mapped_column(String(20), default="VSTEP_3_5", server_default="VSTEP_3_5")
    source: Mapped[str] = mapped_column(String(10), default="SEED")
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    generation_diagnostics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")


class SpeakingExamSession(LibrarySessionMixin, IdentityMixin, Base):
    __tablename__ = "speaking_exam_sessions"
    __table_args__ = (CheckConstraint("mode IN ('FULL_TEST', 'PART1', 'PART2', 'PART3', 'QUICK_PRACTICE')"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_profile: Mapped[str] = mapped_column(String(20), default="VSTEP_3_5", server_default="VSTEP_3_5")
    mode: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")
    access_source: Mapped[str] = mapped_column(String(12), default="LEGACY", server_default="LEGACY")
    current_part: Mapped[int] = mapped_column(Integer, default=1)
    current_sequence: Mapped[int] = mapped_column(Integer, default=0)
    question_set: Mapped[list] = mapped_column(JSONB)
    answers: Mapped[list["SpeakingAnswer"]] = relationship(
        back_populates="session", lazy="selectin", order_by="SpeakingAnswer.sequence_number"
    )
    grading: Mapped["SpeakingGrading | None"] = relationship(
        lazy="selectin", uselist=False, foreign_keys="SpeakingGrading.session_id"
    )


class SpeakingAnswer(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "speaking_answers"
    __table_args__ = (UniqueConstraint("session_id", "sequence_number"),)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("speaking_exam_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[str] = mapped_column(ForeignKey("speaking_questions.id"))
    part: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="RECORDING")
    recording_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    audio_path: Mapped[str | None] = mapped_column(Text)
    normalized_audio_path: Mapped[str | None] = mapped_column(Text)
    audio_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    audio_duration_ms: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(80))
    audio_size: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    transcript_hash: Mapped[str | None] = mapped_column(String(64))
    transcription_key: Mapped[str | None] = mapped_column(String(64), index=True)
    transcription_model: Mapped[str | None] = mapped_column(String(100))
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    audio_analysis: Mapped[dict | None] = mapped_column(JSONB)
    audio_analysis_key: Mapped[str | None] = mapped_column(String(64), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session: Mapped[SpeakingExamSession] = relationship(back_populates="answers")
    grading: Mapped["SpeakingGrading | None"] = relationship(
        lazy="selectin", uselist=False, foreign_keys="SpeakingGrading.answer_id"
    )


class SpeakingGrading(IdentityMixin, Base):
    __tablename__ = "speaking_gradings"
    __table_args__ = (
        CheckConstraint("(session_id IS NULL) <> (answer_id IS NULL)"),
        *(
            CheckConstraint(f"{key}_score IS NULL OR ({key}_score >= 0 AND {key}_score <= 10)")
            for key in ("grammar", "vocabulary", "pronunciation", "fluency", "structures", "overall")
        ),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("speaking_exam_sessions.id", ondelete="CASCADE"), unique=True
    )
    answer_id: Mapped[str | None] = mapped_column(
        ForeignKey("speaking_answers.id", ondelete="CASCADE"), unique=True
    )
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    grammar_score: Mapped[float] = mapped_column(Float)
    vocabulary_score: Mapped[float] = mapped_column(Float)
    pronunciation_score: Mapped[float | None] = mapped_column(Float)
    fluency_score: Mapped[float | None] = mapped_column(Float)
    structures_score: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float)
    estimated_level: Mapped[str] = mapped_column(String(30))
    summary_vi: Mapped[str] = mapped_column(Text)
    strengths: Mapped[list] = mapped_column(JSONB)
    priority_improvements: Mapped[list] = mapped_column(JSONB)
    pronunciation_feedback: Mapped[list] = mapped_column(JSONB)
    fluency_feedback: Mapped[list] = mapped_column(JSONB)
    structure_feedback: Mapped[list] = mapped_column(JSONB)
    content_feedback: Mapped[list] = mapped_column(JSONB)
    vocabulary_suggestions: Mapped[list] = mapped_column(JSONB)
    sentence_corrections: Mapped[list] = mapped_column(JSONB)
    answer_feedback: Mapped[list] = mapped_column(JSONB)
    speaking_frame: Mapped[list] = mapped_column(JSONB)
    corrected_transcript: Mapped[str] = mapped_column(Text)
    improved_b2_answer: Mapped[str] = mapped_column(Text)
    audio_coverage: Mapped[dict] = mapped_column(JSONB)
    ai_model: Mapped[str] = mapped_column(String(100))
    audio_model: Mapped[str | None] = mapped_column(String(100))
    transcription_model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(20))
    errors: Mapped[list["SpeakingError"]] = relationship(lazy="selectin", cascade="all, delete-orphan")


class SpeakingError(IdentityMixin, Base):
    __tablename__ = "speaking_errors"
    grading_id: Mapped[str] = mapped_column(
        ForeignKey("speaking_gradings.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30), index=True)
    subtype: Mapped[str] = mapped_column(String(80))
    original: Mapped[str] = mapped_column(Text)
    corrected: Mapped[str] = mapped_column(Text)
    explanation_vi: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float | None] = mapped_column(Float)
