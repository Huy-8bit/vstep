"""Persist Writing evidence/revisions and pronunciation practice recordings.

Revision ID: e41b6d0a9f22
Revises: c87e4a932b61
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e41b6d0a9f22"
down_revision = "c87e4a932b61"
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.add_column(
        "writing_attempts", sa.Column("grading_work", postgresql.JSONB(), nullable=False, server_default="{}")
    )
    # Existing rows remain explicitly identifiable as results of the original grader.
    op.add_column(
        "writing_gradings", sa.Column("grader_version", sa.String(30), nullable=False, server_default="1.0.0")
    )
    op.add_column("writing_gradings", sa.Column("analysis_prompt_version", sa.String(30), nullable=True))
    op.add_column("writing_gradings", sa.Column("calibration_prompt_version", sa.String(30), nullable=True))
    op.add_column(
        "writing_gradings",
        sa.Column("criterion_evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "writing_gradings",
        sa.Column("analysis_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "writing_grading_revisions",
        *identity(),
        sa.Column(
            "attempt_id",
            sa.String(36),
            sa.ForeignKey("writing_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("grader_version", sa.String(30), nullable=False),
        sa.Column("grading_model", sa.String(100), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_writing_grading_revisions_attempt_id", "writing_grading_revisions", ["attempt_id"])
    op.create_table(
        "writing_calibration_samples",
        *identity(),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        *[
            sa.Column(f"human_{criterion}_score", sa.Float(), nullable=True)
            for criterion in ("task", "organization", "vocabulary", "grammar", "overall")
        ],
        sa.Column("reviewer_count", sa.Integer(), nullable=False),
    )
    op.create_table(
        "pronunciation_practices",
        *identity(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_text", sa.String(500), nullable=False),
        sa.Column("reference_hash", sa.String(64), nullable=False),
        sa.Column(
            "source_answer_id",
            sa.String(36),
            sa.ForeignKey("speaking_answers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_issue_type", sa.String(40), nullable=True),
        sa.Column("audio_path", sa.Text(), nullable=True),
        sa.Column("audio_hash", sa.String(64), nullable=True),
        sa.Column("audio_duration_ms", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("analysis", postgresql.JSONB(), nullable=True),
        sa.Column("analysis_key", sa.String(64), nullable=True),
        sa.Column("pronunciation_score", sa.Float(), nullable=True),
        sa.Column("fluency_score", sa.Float(), nullable=True),
        sa.Column("audio_model", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(30), nullable=True),
        sa.Column("client_request_id", sa.String(36), nullable=False),
        sa.UniqueConstraint("user_id", "client_request_id"),
    )
    for column in ("user_id", "reference_hash", "analysis_key"):
        op.create_index(f"ix_pronunciation_practices_{column}", "pronunciation_practices", [column])


def downgrade():
    op.drop_table("pronunciation_practices")
    op.drop_table("writing_calibration_samples")
    op.drop_table("writing_grading_revisions")
    for column in (
        "analysis_snapshot",
        "criterion_evidence",
        "calibration_prompt_version",
        "analysis_prompt_version",
        "grader_version",
    ):
        op.drop_column("writing_gradings", column)
    op.drop_column("writing_attempts", "grading_work")
