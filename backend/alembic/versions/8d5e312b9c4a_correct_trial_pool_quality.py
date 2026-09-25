"""Ensure the first free Writing pool contains only reviewed questions.

Revision ID: 8d5e312b9c4a
Revises: 7ca4f1d2b890
"""

from alembic import op

revision = "8d5e312b9c4a"
down_revision = "7ca4f1d2b890"
branch_labels = None
depends_on = None


def upgrade():
    # Early legacy seed rows have no quality metadata. They must never consume a trial.
    op.execute("""
        UPDATE writing_questions SET access_tier = 'VIP', available_for_free_trial = false
        WHERE owner_id IS NULL AND source = 'SEED' AND available_for_free_trial = true
          AND COALESCE(generation_diagnostics ->> 'quality_valid', 'false') != 'true'
    """)
    op.execute("""
        WITH candidates AS (
          SELECT id FROM writing_questions
          WHERE owner_id IS NULL AND source = 'SEED' AND task_type = 1
            AND generation_diagnostics ->> 'quality_valid' = 'true'
            AND available_for_free_trial = false
          ORDER BY created_at, id
          LIMIT GREATEST(0, 4 - (SELECT count(*) FROM writing_questions
              WHERE owner_id IS NULL AND task_type = 1 AND is_published = true
                AND available_for_free_trial = true
                AND generation_diagnostics ->> 'quality_valid' = 'true'))
        )
        UPDATE writing_questions SET access_tier = 'FREE_TRIAL', available_for_free_trial = true
        WHERE id IN (SELECT id FROM candidates)
    """)


def downgrade():
    # Publication decisions are business data and are intentionally preserved.
    pass
