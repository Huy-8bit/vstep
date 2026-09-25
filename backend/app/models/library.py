"""Private library records and immutable revisions; practice uses the existing skill entities."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin, UpdatedMixin


class LibrarySessionMixin:
    library_question_id: Mapped[str | None] = mapped_column(ForeignKey("library_questions.id"), index=True)
    library_revision: Mapped[int | None] = mapped_column(Integer)
    library_title: Mapped[str | None] = mapped_column(String(300))


class PrivateQuestionMixin(LibrarySessionMixin):
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    presentation: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    access_tier: Mapped[str] = mapped_column(String(12), default="VIP", server_default="VIP")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    available_for_free_trial: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class QuestionCollection(IdentityMixin, Base):
    __tablename__ = "question_collections"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))


class LibraryQuestion(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "library_questions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    skill: Mapped[str] = mapped_column(String(10), index=True)
    part: Mapped[str] = mapped_column(String(20), index=True)
    topic: Mapped[str] = mapped_column(String(40), default="other")
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    collection_id: Mapped[str | None] = mapped_column(
        ForeignKey("question_collections.id", ondelete="SET NULL")
    )
    source_type: Mapped[str] = mapped_column(String(20), default="manual")
    source_name: Mapped[str | None] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    asset_ids: Mapped[list] = mapped_column(JSONB, default=list)
    content: Mapped[dict] = mapped_column(JSONB)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LibraryRevision(IdentityMixin, Base):
    __tablename__ = "library_revisions"
    __table_args__ = (UniqueConstraint("question_id", "revision"),)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("library_questions.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    document: Mapped[dict] = mapped_column(JSONB)


class QuestionImportFile(IdentityMixin, Base):
    __tablename__ = "question_import_files"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(250))
    mime_type: Mapped[str] = mapped_column(String(40))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(Text)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
