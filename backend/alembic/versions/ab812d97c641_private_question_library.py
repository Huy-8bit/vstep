"""Private question library, immutable practice revisions and incomplete reading keys.

Revision ID: ab812d97c641
Revises: f729a310c058
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "ab812d97c641"
down_revision = "f729a310c058"
branch_labels = depends_on = None


def identity():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "question_collections",
        *identity(),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
    )
    op.create_table(
        "question_import_files",
        *identity(),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("filename", sa.String(250), nullable=False),
        sa.Column("mime_type", sa.String(40), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("page_count", sa.Integer, nullable=False),
    )
    op.create_table(
        "library_questions",
        *identity(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("skill", sa.String(10), nullable=False, index=True),
        sa.Column("part", sa.String(20), nullable=False, index=True),
        sa.Column("topic", sa.String(40), nullable=False),
        sa.Column("tags", JSONB, nullable=False),
        sa.Column("favorite", sa.Boolean, nullable=False),
        sa.Column(
            "collection_id", sa.String(36), sa.ForeignKey("question_collections.id", ondelete="SET NULL")
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_name", sa.String(300)),
        sa.Column("source_url", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("asset_ids", JSONB, nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "library_revisions",
        *identity(),
        sa.Column(
            "question_id", sa.String(36), sa.ForeignKey("library_questions.id"), nullable=False, index=True
        ),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("document", JSONB, nullable=False),
        sa.UniqueConstraint("question_id", "revision"),
    )
    for table in (
        "writing_questions",
        "speaking_questions",
        "reading_passages",
        "exam_sessions",
        "speaking_exam_sessions",
        "reading_exam_sessions",
    ):
        op.add_column(
            table, sa.Column("library_question_id", sa.String(36), sa.ForeignKey("library_questions.id"))
        )
        op.create_index(f"ix_{table}_library_question_id", table, ["library_question_id"])
        op.add_column(table, sa.Column("library_revision", sa.Integer))
        op.add_column(table, sa.Column("library_title", sa.String(300)))
        if table in ("writing_questions", "speaking_questions", "reading_passages"):
            op.add_column(
                table, sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"))
            )
            op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
            op.add_column(table, sa.Column("presentation", JSONB, nullable=False, server_default="{}"))
    # PostgreSQL assigns names to the legacy unnamed constraints; locate by expression.
    for constraint in sa.inspect(op.get_bind()).get_check_constraints("writing_questions"):
        if "minimum_words" in constraint["sqltext"]:
            op.drop_constraint(constraint["name"], "writing_questions", type_="check")
    op.create_check_constraint("writing_minimum_words_positive", "writing_questions", "minimum_words > 0")
    op.add_column(
        "reading_questions",
        sa.Column("answer_key_source", sa.String(20), nullable=False, server_default="provided"),
    )
    for column, type_ in (("correct_answer", sa.String(1)), ("explanation_vi", sa.Text), ("evidence", JSONB)):
        op.alter_column("reading_questions", column, existing_type=type_, nullable=True)
    for column in ("score", "accuracy"):
        op.alter_column("reading_results", column, existing_type=sa.Float, nullable=True)
    op.add_column(
        "reading_results", sa.Column("scorable_count", sa.Integer, nullable=False, server_default="0")
    )
    op.add_column(
        "reading_results", sa.Column("unscored_count", sa.Integer, nullable=False, server_default="0")
    )
    op.execute(
        "UPDATE reading_results r SET scorable_count = s.question_count FROM reading_exam_sessions s WHERE s.id = r.session_id"
    )
    op.alter_column("reading_results", "scorable_count", server_default=None)
    op.alter_column("reading_results", "unscored_count", server_default=None)


def downgrade():
    # A rollback would discard private content and cannot restore nullable results safely.
    raise RuntimeError(
        "Preserve library/history data: restore an explicit backup instead of destructive downgrade."
    )
