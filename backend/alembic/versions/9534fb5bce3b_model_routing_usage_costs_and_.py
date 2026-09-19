"""Per-call cost ledger and persisted model evaluation runs; preserve historical usage."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "9534fb5bce3b"
down_revision = "d3b0729f418a"
branch_labels = depends_on = None


def upgrade():
    for name, kind, default in (
        ("reasoning_effort", sa.String(20), None),
        ("cached_input_tokens", sa.Integer(), "0"),
        ("reasoning_tokens", sa.Integer(), "0"),
        ("estimated_cost_usd", sa.Numeric(14, 8), None),
        ("attempt_id", sa.String(36), None),
        ("category", sa.String(30), "legacy"),
        ("evaluation_id", sa.String(36), None),
        ("details", postgresql.JSONB(), "{}"),
    ):
        op.add_column(
            "ai_usage_logs", sa.Column(name, kind, nullable=default is None, server_default=default)
        )
    op.alter_column("ai_usage_logs", "user_id", nullable=True)
    op.alter_column("ai_usage_logs", "operation", type_=sa.String(60))
    op.drop_constraint("ai_usage_logs_user_id_fkey", "ai_usage_logs", type_="foreignkey")
    op.create_foreign_key(
        "ai_usage_logs_user_id_fkey", "ai_usage_logs", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_ai_usage_time_category", "ai_usage_logs", ["created_at", "category"])
    op.create_index("ix_ai_usage_user_attempt", "ai_usage_logs", ["user_id", "attempt_id"])
    op.create_table(
        "grading_model_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("reasoning_effort", sa.String(20), nullable=False),
        sa.Column("dataset_version", sa.String(100), nullable=False),
        sa.Column("dataset_hash", sa.String(64), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=False),
        sa.Column("versions", postgresql.JSONB(), nullable=False),
    )


def downgrade():
    # Unattributed evaluation/erased-user logs cannot fit the old mandatory user schema.
    # Refuse a destructive downgrade rather than silently delete billing history.
    if op.get_bind().scalar(
        sa.text("SELECT count(*) FROM ai_usage_logs WHERE user_id IS NULL OR length(operation)>30")
    ):
        raise RuntimeError("Export newer usage records before downgrading; no billing history was deleted.")
    op.drop_table("grading_model_evaluations")
    op.drop_index("ix_ai_usage_user_attempt", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_time_category", table_name="ai_usage_logs")
    op.drop_constraint("ai_usage_logs_user_id_fkey", "ai_usage_logs", type_="foreignkey")
    op.create_foreign_key(
        "ai_usage_logs_user_id_fkey", "ai_usage_logs", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.alter_column("ai_usage_logs", "user_id", nullable=False)
    op.alter_column("ai_usage_logs", "operation", type_=sa.String(30))
    for name in (
        "reasoning_effort",
        "cached_input_tokens",
        "reasoning_tokens",
        "estimated_cost_usd",
        "attempt_id",
        "category",
        "evaluation_id",
        "details",
    ):
        op.drop_column("ai_usage_logs", name)
