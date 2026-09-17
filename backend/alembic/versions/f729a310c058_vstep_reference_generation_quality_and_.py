"""vstep reference generation quality and vocabulary coach"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f729a310c058"
down_revision: str | None = "e41b6d0a9f22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_vocabulary_items",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("headword", sa.String(length=150), nullable=False),
        sa.Column("phrase", sa.String(length=250), nullable=False),
        sa.Column("part_of_speech", sa.String(length=100), nullable=False),
        sa.Column("meaning_vi", sa.Text(), nullable=False),
        sa.Column("meaning_in_context_vi", sa.Text(), nullable=False),
        sa.Column("register", sa.String(length=40), nullable=False),
        sa.Column("collocations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("common_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_skill", sa.String(length=20), nullable=False),
        sa.Column("source_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("source_topic", sa.String(length=50), nullable=False),
        sa.Column("user_original_text", sa.Text(), nullable=True),
        sa.Column("improved_text", sa.Text(), nullable=True),
        sa.Column("example_sentence", sa.Text(), nullable=False),
        sa.Column("why_learn_this_vi", sa.Text(), nullable=False),
        sa.Column("issue_type", sa.String(length=40), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("exercise_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mastery_level", sa.String(length=20), nullable=False),
        sa.Column("mastery_step", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("correct_review_count", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "fingerprint"),
    )
    op.create_index(
        op.f("ix_user_vocabulary_items_mastery_level"),
        "user_vocabulary_items",
        ["mastery_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_vocabulary_items_next_review_at"),
        "user_vocabulary_items",
        ["next_review_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_vocabulary_items_source_topic"), "user_vocabulary_items", ["source_topic"], unique=False
    )
    op.create_index(
        op.f("ix_user_vocabulary_items_user_id"), "user_vocabulary_items", ["user_id"], unique=False
    )
    op.create_table(
        "vocabulary_recommendation_batches",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_skill", sa.String(length=20), nullable=False),
        sa.Column("source_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("source_topic", sa.String(length=50), nullable=False),
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "cache_key"),
    )
    op.create_index(
        op.f("ix_vocabulary_recommendation_batches_user_id"),
        "vocabulary_recommendation_batches",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "vocabulary_item_sources",
        sa.Column("item_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("source_skill", sa.String(length=20), nullable=False),
        sa.Column("source_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("source_topic", sa.String(length=50), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["vocabulary_recommendation_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["user_vocabulary_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id", "item_index"),
    )
    op.create_index(
        op.f("ix_vocabulary_item_sources_item_id"), "vocabulary_item_sources", ["item_id"], unique=False
    )
    op.create_table(
        "vocabulary_reviews",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("item_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("prompt", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=True),
        sa.Column("feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessment_model", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("client_request_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["user_vocabulary_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_request_id"),
    )
    op.create_index(op.f("ix_vocabulary_reviews_item_id"), "vocabulary_reviews", ["item_id"], unique=False)
    op.create_index(op.f("ix_vocabulary_reviews_user_id"), "vocabulary_reviews", ["user_id"], unique=False)
    op.add_column(
        "reading_exam_sessions",
        sa.Column(
            "blueprint_diagnostics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "reading_passages",
        sa.Column(
            "generation_diagnostics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "reading_questions", sa.Column("placement", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "speaking_questions",
        sa.Column(
            "generation_diagnostics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "writing_calibration_samples", sa.Column("question_id", sa.String(length=36), nullable=True)
    )
    op.add_column("writing_calibration_samples", sa.Column("task_type", sa.Integer(), nullable=True))
    op.add_column("writing_calibration_samples", sa.Column("notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_writing_calibration_question",
        "writing_calibration_samples",
        "writing_questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "writing_questions",
        sa.Column(
            "generation_diagnostics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column("writing_questions", sa.Column("stimulus", sa.Text(), nullable=True))
    op.add_column("writing_questions", sa.Column("response_instruction", sa.Text(), nullable=True))
    op.add_column("writing_questions", sa.Column("genre", sa.String(length=20), nullable=True))
    op.add_column("writing_questions", sa.Column("register", sa.String(length=20), nullable=True))
    op.add_column(
        "writing_questions", sa.Column("recipient_relationship", sa.String(length=50), nullable=True)
    )
    op.add_column("writing_questions", sa.Column("purpose", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("writing_questions", "purpose")
    op.drop_column("writing_questions", "recipient_relationship")
    op.drop_column("writing_questions", "register")
    op.drop_column("writing_questions", "genre")
    op.drop_column("writing_questions", "response_instruction")
    op.drop_column("writing_questions", "stimulus")
    op.drop_column("writing_questions", "generation_diagnostics")
    op.drop_constraint("fk_writing_calibration_question", "writing_calibration_samples", type_="foreignkey")
    op.drop_column("writing_calibration_samples", "notes")
    op.drop_column("writing_calibration_samples", "task_type")
    op.drop_column("writing_calibration_samples", "question_id")
    op.drop_column("speaking_questions", "generation_diagnostics")
    op.drop_column("reading_questions", "placement")
    op.drop_column("reading_passages", "generation_diagnostics")
    op.drop_column("reading_exam_sessions", "blueprint_diagnostics")
    op.drop_index(op.f("ix_vocabulary_reviews_user_id"), table_name="vocabulary_reviews")
    op.drop_index(op.f("ix_vocabulary_reviews_item_id"), table_name="vocabulary_reviews")
    op.drop_table("vocabulary_reviews")
    op.drop_index(op.f("ix_vocabulary_item_sources_item_id"), table_name="vocabulary_item_sources")
    op.drop_table("vocabulary_item_sources")
    op.drop_index(
        op.f("ix_vocabulary_recommendation_batches_user_id"), table_name="vocabulary_recommendation_batches"
    )
    op.drop_table("vocabulary_recommendation_batches")
    op.drop_index(op.f("ix_user_vocabulary_items_user_id"), table_name="user_vocabulary_items")
    op.drop_index(op.f("ix_user_vocabulary_items_source_topic"), table_name="user_vocabulary_items")
    op.drop_index(op.f("ix_user_vocabulary_items_next_review_at"), table_name="user_vocabulary_items")
    op.drop_index(op.f("ix_user_vocabulary_items_mastery_level"), table_name="user_vocabulary_items")
    op.drop_table("user_vocabulary_items")
