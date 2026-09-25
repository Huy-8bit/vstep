"""Add roles, time-bound VIP, trials, payments and bank publication metadata.

Revision ID: 7ca4f1d2b890
Revises: 9534fb5bce3b
"""

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "7ca4f1d2b890"
down_revision = "9534fb5bce3b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("name", sa.String(160)))
    op.add_column("users", sa.Column("role", sa.String(12), nullable=False, server_default="USER"))
    op.add_column("users", sa.Column("status", sa.String(12), nullable=False, server_default="ACTIVE"))
    op.add_column(
        "users", sa.Column("is_test_account", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("users", sa.Column("learning_goal", sa.String(240)))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.create_check_constraint("ck_users_role", "users", "role IN ('USER','ADMIN')")
    op.create_check_constraint("ck_users_status", "users", "status IN ('ACTIVE','DISABLED')")

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_vnd", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("duration_days > 0"),
        sa.CheckConstraint("price_vnd >= 0"),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "plan_id",
            sa.String(36),
            sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_payment_id", sa.String(120), unique=True),
        sa.Column("amount_vnd", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("amount_vnd >= 0"),
        sa.CheckConstraint("status IN ('PENDING','PAID','FAILED','CANCELLED','EXPIRED','REFUNDED')"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_table(
        "user_entitlements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("subscription_plans.id", ondelete="SET NULL")),
        sa.Column("entitlement_type", sa.String(20), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("created_by_admin_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column(
            "payment_id", sa.String(36), sa.ForeignKey("payments.id", ondelete="SET NULL"), unique=True
        ),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("expires_at > starts_at"),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED')"),
    )
    op.create_index("ix_user_entitlements_user_id", "user_entitlements", ["user_id"])
    op.create_index("ix_user_entitlements_expires_at", "user_entitlements", ["expires_at"])
    op.create_table(
        "user_trial_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(32), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "feature_code"),
        sa.CheckConstraint("used_count >= 0"),
    )
    op.create_table(
        "vip_daily_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(32), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "feature_code", "day"),
        sa.CheckConstraint("used_count >= 0"),
    )
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"])
    op.create_table(
        "product_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_product_events_user_id", "product_events", ["user_id"])
    op.create_index("ix_product_events_name", "product_events", ["name"])

    op.add_column(
        "exam_sessions", sa.Column("access_source", sa.String(12), nullable=False, server_default="LEGACY")
    )
    op.add_column(
        "speaking_exam_sessions",
        sa.Column("access_source", sa.String(12), nullable=False, server_default="LEGACY"),
    )
    op.add_column(
        "reading_exam_sessions",
        sa.Column("access_source", sa.String(12), nullable=False, server_default="LEGACY"),
    )

    for table in ("writing_questions", "speaking_questions", "reading_passages"):
        op.add_column(table, sa.Column("access_tier", sa.String(12), nullable=False, server_default="VIP"))
        op.add_column(
            table, sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        op.add_column(
            table,
            sa.Column("available_for_free_trial", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.add_column(
            table, sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        op.create_check_constraint(
            f"ck_{table}_access_tier", table, "access_tier IN ('FREE_TRIAL','VIP','INTERNAL')"
        )
    op.execute("""
        UPDATE writing_questions SET access_tier = 'FREE_TRIAL', available_for_free_trial = true
        WHERE id IN (SELECT id FROM writing_questions WHERE owner_id IS NULL AND source = 'SEED' AND task_type = 1
                     AND generation_diagnostics ->> 'quality_valid' = 'true'
                     ORDER BY created_at, id LIMIT 4)
    """)
    op.execute("""
        UPDATE speaking_questions SET access_tier = 'FREE_TRIAL', available_for_free_trial = true
        WHERE id IN (SELECT id FROM speaking_questions WHERE owner_id IS NULL AND source = 'SEED' AND part = 1
                     ORDER BY created_at, id LIMIT 4)
    """)
    plan_table = sa.table(
        "subscription_plans",
        sa.column("id"),
        sa.column("created_at"),
        sa.column("updated_at"),
        sa.column("code"),
        sa.column("name"),
        sa.column("duration_days"),
        sa.column("price_vnd"),
        sa.column("is_active"),
        sa.column("sort_order"),
    )
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    op.bulk_insert(
        plan_table,
        [
            dict(
                id=str(uuid4()),
                created_at=now,
                updated_at=now,
                code="VIP_3_DAYS",
                name="VIP 3 ngày",
                duration_days=3,
                price_vnd=50000,
                is_active=True,
                sort_order=1,
            ),
            dict(
                id=str(uuid4()),
                created_at=now,
                updated_at=now,
                code="VIP_7_DAYS",
                name="VIP 7 ngày",
                duration_days=7,
                price_vnd=100000,
                is_active=True,
                sort_order=2,
            ),
            dict(
                id=str(uuid4()),
                created_at=now,
                updated_at=now,
                code="VIP_30_DAYS",
                name="VIP 30 ngày",
                duration_days=30,
                price_vnd=150000,
                is_active=True,
                sort_order=3,
            ),
        ],
    )


def downgrade():
    for table in ("exam_sessions", "speaking_exam_sessions", "reading_exam_sessions"):
        op.drop_column(table, "access_source")
    for table in ("writing_questions", "speaking_questions", "reading_passages"):
        op.drop_constraint(f"ck_{table}_access_tier", table, type_="check")
        for name in ("is_featured", "available_for_free_trial", "is_published", "access_tier"):
            op.drop_column(table, name)
    for table in (
        "product_events",
        "admin_audit_logs",
        "vip_daily_usage",
        "user_trial_usage",
        "user_entitlements",
        "payments",
        "subscription_plans",
    ):
        op.drop_table(table)
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.drop_constraint("ck_users_role", "users", type_="check")
    for name in ("last_login_at", "learning_goal", "is_test_account", "status", "role", "name"):
        op.drop_column("users", name)
