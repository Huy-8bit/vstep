"""Separate multilevel exam profiles from historical CEFR difficulty labels.

Revision ID: c87e4a932b61
Revises: 5c96e8660369
"""

import sqlalchemy as sa

from alembic import op

revision = "c87e4a932b61"
down_revision = "5c96e8660369"
branch_labels = None
depends_on = None

PROFILE_TABLES = (
    "writing_questions",
    "exam_sessions",
    "speaking_questions",
    "speaking_exam_sessions",
    "reading_passages",
    "reading_questions",
    "reading_exam_sessions",
)
LEGACY_TABLES = (
    ("writing_questions", 10),
    ("speaking_questions", 10),
    ("reading_passages", 5),
    ("reading_questions", 5),
    ("reading_exam_sessions", 5),
)
# Editorial review of these eight known original texts. Do not infer CEFR calibration
# or assign bands to old AI passages from their obsolete B1/B2/C1 label.
SEED_BANDS = (
    ("A Library Beyond Its Walls", "ACCESSIBLE"),
    ("Saturday at the Repair Table", "ACCESSIBLE"),
    ("When the Field Sends a Message", "MODERATE"),
    ("A Garden Above the Street", "MODERATE"),
    ("The Meeting That Began in Silence", "CHALLENGING"),
    ("Whose Words Are Beside the Object?", "CHALLENGING"),
    ("The Value of a Qualified Answer", "ADVANCED"),
    ("Many Observers, Uneven Evidence", "ADVANCED"),
)


def upgrade():
    for table in PROFILE_TABLES:
        op.add_column(
            table, sa.Column("test_profile", sa.String(20), nullable=False, server_default="VSTEP_3_5")
        )
    for table, length in LEGACY_TABLES:
        op.alter_column(
            table,
            "difficulty",
            existing_type=sa.String(length),
            nullable=True,
            comment="Deprecated historical label. Not used for generation or candidate ability.",
        )
    for table in ("reading_passages", "reading_questions"):
        op.add_column(table, sa.Column("internal_difficulty_band", sa.String(20), nullable=True))
    op.create_index(
        "ix_reading_passages_internal_difficulty_band", "reading_passages", ["internal_difficulty_band"]
    )
    op.add_column("reading_exam_sessions", sa.Column("blueprint_version", sa.String(30), nullable=True))
    connection = op.get_bind()
    for title, band in SEED_BANDS:
        connection.execute(
            sa.text(
                "UPDATE reading_passages SET internal_difficulty_band = :band WHERE source = 'SEED' AND title = :title"
            ),
            {"title": title, "band": band},
        )
    # Item metadata is reloaded idempotently by reading_seed at startup. Existing answer keys,
    # paragraph text, question IDs, session ordering, results and audio are untouched.


def downgrade():
    # Preserve nullable historical difficulty values: new material has no CEFR difficulty to restore.
    op.drop_column("reading_exam_sessions", "blueprint_version")
    op.drop_index("ix_reading_passages_internal_difficulty_band", table_name="reading_passages")
    for table in ("reading_questions", "reading_passages"):
        op.drop_column(table, "internal_difficulty_band")
    for table in reversed(PROFILE_TABLES):
        op.drop_column(table, "test_profile")
