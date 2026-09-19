"""Allow natural generated purpose descriptions without truncating learner questions.

Revision ID: d3b0729f418a
Revises: 63890193a7ac
"""

import sqlalchemy as sa

from alembic import op

revision = "d3b0729f418a"
down_revision = "63890193a7ac"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "writing_questions", "purpose", existing_type=sa.String(100), type_=sa.Text(), existing_nullable=True
    )


def downgrade():
    # Fail rather than silently truncate any purpose written after the upgrade.
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM writing_questions WHERE length(purpose) > 100) THEN RAISE EXCEPTION 'Cannot narrow purpose: values longer than 100 characters exist'; END IF; END $$"
    )
    op.alter_column(
        "writing_questions", "purpose", existing_type=sa.Text(), type_=sa.String(100), existing_nullable=True
    )
