"""Commercial records. Access is always derived from time-bound entitlements."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdentityMixin, UpdatedMixin


class SubscriptionPlan(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "subscription_plans"
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    duration_days: Mapped[int] = mapped_column(Integer)
    price_vnd: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (CheckConstraint("duration_days > 0"), CheckConstraint("price_vnd >= 0"))


class Payment(IdentityMixin, Base):
    __tablename__ = "payments"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"))
    provider: Mapped[str] = mapped_column(String(30), default="MANUAL")
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    amount_vnd: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="VND")
    status: Mapped[str] = mapped_column(String(12), default="PENDING", index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (CheckConstraint("amount_vnd >= 0"),)


class UserEntitlement(IdentityMixin, Base):
    __tablename__ = "user_entitlements"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[str | None] = mapped_column(ForeignKey("subscription_plans.id", ondelete="SET NULL"))
    entitlement_type: Mapped[str] = mapped_column(String(20), default="VIP")
    source: Mapped[str] = mapped_column(String(20))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(12), default="ACTIVE")
    created_by_admin_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    payment_id: Mapped[str | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"), unique=True
    )
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (CheckConstraint("expires_at > starts_at"),)


class TrialUsage(IdentityMixin, UpdatedMixin, Base):
    __tablename__ = "user_trial_usage"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    feature_code: Mapped[str] = mapped_column(String(32))
    max_uses: Mapped[int] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("user_id", "feature_code"), CheckConstraint("used_count >= 0"))


class VipDailyUsage(IdentityMixin, Base):
    __tablename__ = "vip_daily_usage"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    feature_code: Mapped[str] = mapped_column(String(32))
    day: Mapped[date] = mapped_column(Date)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("user_id", "feature_code", "day"), CheckConstraint("used_count >= 0"))


class AdminAuditLog(IdentityMixin, Base):
    __tablename__ = "admin_audit_logs"
    admin_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(50), index=True)
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class ProductEvent(IdentityMixin, Base):
    __tablename__ = "product_events"
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(60), index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
