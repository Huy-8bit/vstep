"""Keep immutable revisions while a library exists; support existing account cascade cleanup."""

from alembic import op
import sqlalchemy as sa

revision = "bcdf7614289e"
down_revision = "ab812d97c641"
branch_labels = depends_on = None


def upgrade():
    for fk in sa.inspect(op.get_bind()).get_foreign_keys("library_revisions"):
        if fk["constrained_columns"] == ["question_id"]:
            op.drop_constraint(fk["name"], "library_revisions", type_="foreignkey")
    op.create_foreign_key(
        "library_revisions_question_id_fkey",
        "library_revisions",
        "library_questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("library_revisions_question_id_fkey", "library_revisions", type_="foreignkey")
    op.create_foreign_key(
        "library_revisions_question_id_fkey",
        "library_revisions",
        "library_questions",
        ["question_id"],
        ["id"],
    )
