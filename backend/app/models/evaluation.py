from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin


class GradingModelEvaluation(IdentityMixin, Base):
    __tablename__ = "grading_model_evaluations"
    model: Mapped[str] = mapped_column(String(100))
    reasoning_effort: Mapped[str] = mapped_column(String(20))
    dataset_version: Mapped[str] = mapped_column(String(100))
    dataset_hash: Mapped[str] = mapped_column(String(64))
    sample_count: Mapped[int] = mapped_column(Integer)
    metrics: Mapped[dict] = mapped_column(JSONB)
    results: Mapped[list] = mapped_column(JSONB)
    versions: Mapped[dict] = mapped_column(JSONB)
