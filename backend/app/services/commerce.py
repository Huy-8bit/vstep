"""Payment-independent VIP activation and auditable manual operations."""

from abc import ABC, abstractmethod
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.db.base import utcnow
from app.models import User
from app.models.commerce import AdminAuditLog, Payment, ProductEvent, SubscriptionPlan, UserEntitlement


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(self, payment: Payment) -> dict: ...

    @abstractmethod
    async def verify_payment(self, payment: Payment) -> bool: ...

    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str | None) -> str: ...

    @abstractmethod
    async def query_payment(self, payment: Payment) -> str: ...


class ManualPaymentProvider(PaymentProvider):
    async def create_payment(self, payment: Payment) -> dict:
        return {
            "payment_id": payment.id,
            "status": "PENDING",
            "instructions_vi": "Liên hệ hỗ trợ để được hướng dẫn chuyển khoản và xác nhận thủ công.",
        }

    async def verify_payment(self, payment: Payment) -> bool:
        return False  # A manual payment is confirmed only by an ADMIN action.

    async def handle_webhook(self, payload: bytes, signature: str | None) -> str:
        raise AppError(501, "Chưa cấu hình cổng thanh toán tự động.", "PAYMENT_PROVIDER_UNAVAILABLE")

    async def query_payment(self, payment: Payment) -> str:
        return payment.status


def plan_view(plan: SubscriptionPlan):
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "duration_days": plan.duration_days,
        "price_vnd": plan.price_vnd,
        "is_active": plan.is_active,
        "sort_order": plan.sort_order,
    }


def payment_view(payment: Payment):
    return {
        "id": payment.id,
        "user_id": payment.user_id,
        "plan_id": payment.plan_id,
        "provider": payment.provider,
        "provider_payment_id": payment.provider_payment_id,
        "amount_vnd": payment.amount_vnd,
        "currency": payment.currency,
        "status": payment.status,
        "created_at": payment.created_at,
        "paid_at": payment.paid_at,
        "plan_snapshot": payment.details.get("plan_snapshot", {}),
    }


def entitlement_view(row: UserEntitlement):
    return {
        "id": row.id,
        "user_id": row.user_id,
        "plan_id": row.plan_id,
        "source": row.source,
        "status": row.status,
        "starts_at": row.starts_at,
        "expires_at": row.expires_at,
        "payment_id": row.payment_id,
        "reason": row.details.get("reason"),
    }


class CommerceService:
    def __init__(self, db):
        self.db = db

    async def plan(self, code: str):
        plan = await self.db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.code == code, SubscriptionPlan.is_active.is_(True)
            )
        )
        if not plan:
            raise AppError(404, "Gói VIP không còn được bán.", "PLAN_UNAVAILABLE")
        return plan

    async def create_pending(self, user_id: str, plan_code: str, admin_id: str | None = None):
        await self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        plan = await self.plan(plan_code)
        existing = await self.db.scalar(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.plan_id == plan.id,
                Payment.provider == "MANUAL",
                Payment.status == "PENDING",
                Payment.created_at > utcnow() - timedelta(hours=1),
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        if existing:
            return existing
        payment = Payment(
            user_id=user_id,
            plan_id=plan.id,
            provider="MANUAL",
            amount_vnd=plan.price_vnd,
            currency="VND",
            status="PENDING",
            details={
                "plan_snapshot": {
                    "plan_code": plan.code,
                    "plan_name": plan.name,
                    "duration_days": plan.duration_days,
                    "price_vnd": plan.price_vnd,
                }
            },
        )
        self.db.add(payment)
        await self.db.flush()
        self.db.add(
            ProductEvent(
                user_id=user_id,
                name="CHECKOUT_STARTED",
                details={"payment_id": payment.id, "plan_code": plan.code},
            )
        )
        if admin_id:
            self.db.add(
                AdminAuditLog(
                    admin_user_id=admin_id,
                    action="CREATE_MANUAL_PAYMENT",
                    target_type="PAYMENT",
                    target_id=payment.id,
                    details={"user_id": user_id, "plan_code": plan.code},
                )
            )
        await self.db.commit()
        return payment

    async def grant(
        self,
        user_id: str,
        duration_days: int,
        source: str,
        admin_id: str | None = None,
        reason: str = "",
        plan_id: str | None = None,
        payment_id: str | None = None,
    ):
        user = await self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        if not user:
            raise AppError(404, "Không tìm thấy người dùng.")
        if payment_id:
            existing = await self.db.scalar(
                select(UserEntitlement).where(UserEntitlement.payment_id == payment_id)
            )
            if existing:
                return existing
        now = utcnow()
        # Include queued renewals. A second purchase before the first renewal starts
        # must extend the tail, not overlap the already queued interval.
        from sqlalchemy import func

        expiry = await self.db.scalar(
            select(func.max(UserEntitlement.expires_at)).where(
                UserEntitlement.user_id == user_id,
                UserEntitlement.entitlement_type == "VIP",
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.expires_at > now,
            )
        )
        starts_at = max(now, expiry) if expiry else now
        row = UserEntitlement(
            user_id=user_id,
            plan_id=plan_id,
            entitlement_type="VIP",
            source=source,
            starts_at=starts_at,
            expires_at=starts_at + timedelta(days=duration_days),
            status="ACTIVE",
            created_by_admin_id=admin_id,
            payment_id=payment_id,
            details={"reason": reason},
        )
        self.db.add(row)
        await self.db.flush()
        self.db.add(
            ProductEvent(
                user_id=user_id, name="VIP_ACTIVATED", details={"entitlement_id": row.id, "source": source}
            )
        )
        if admin_id:
            self.db.add(
                AdminAuditLog(
                    admin_user_id=admin_id,
                    action="EXTEND_VIP" if expiry else "GRANT_VIP",
                    target_type="USER",
                    target_id=user_id,
                    details={
                        "days": duration_days,
                        "source": source,
                        "reason": reason,
                        "expires_at": row.expires_at.isoformat(),
                        "payment_id": payment_id,
                    },
                )
            )
        return row

    async def confirm_manual(self, payment_id: str, admin_id: str, reference: str, reason: str):
        reference = reference.strip()
        if len(reference) < 3:
            raise AppError(
                422, "Cần mã giao dịch đã đối soát (ít nhất 3 ký tự).", "PAYMENT_REFERENCE_REQUIRED"
            )
        payment = await self.db.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
        if not payment or payment.provider != "MANUAL":
            raise AppError(404, "Không tìm thấy thanh toán thủ công.")
        if payment.status == "PAID":
            entitlement = await self.db.scalar(
                select(UserEntitlement).where(UserEntitlement.payment_id == payment.id)
            )
            if not entitlement:
                raise AppError(
                    409,
                    "Thanh toán đã ghi nhận nhưng quyền VIP chưa có. Cần kiểm tra vận hành.",
                    "PAYMENT_INCONSISTENT",
                )
            return payment, entitlement
        if payment.status != "PENDING":
            raise AppError(409, "Chỉ xác nhận thanh toán đang chờ.", "PAYMENT_CLOSED")
        duplicate = await self.db.scalar(
            select(Payment.id)
            .where(Payment.provider_payment_id == reference, Payment.id != payment.id)
            .limit(1)
        )
        if duplicate:
            raise AppError(
                409, "Mã giao dịch này đã được dùng cho thanh toán khác.", "PAYMENT_REFERENCE_DUPLICATE"
            )
        plan = await self.db.get(SubscriptionPlan, payment.plan_id)
        snapshot = payment.details["plan_snapshot"]
        if payment.amount_vnd != snapshot["price_vnd"] or snapshot["duration_days"] <= 0:
            raise AppError(409, "Ảnh chụp giá của thanh toán không hợp lệ.", "PAYMENT_INCONSISTENT")
        payment.status = "PAID"
        payment.paid_at = utcnow()
        payment.provider_payment_id = reference or None
        entitlement = await self.grant(
            payment.user_id, snapshot["duration_days"], "PURCHASE", admin_id, reason, plan.id, payment.id
        )
        self.db.add(
            ProductEvent(
                user_id=payment.user_id,
                name="PAYMENT_COMPLETED",
                details={"payment_id": payment.id, "amount_vnd": payment.amount_vnd},
            )
        )
        self.db.add(
            AdminAuditLog(
                admin_user_id=admin_id,
                action="MANUAL_PAYMENT",
                target_type="PAYMENT",
                target_id=payment.id,
                details={"reference": reference, "reason": reason, "amount_vnd": payment.amount_vnd},
            )
        )
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(
                409, "Mã giao dịch đã được xác nhận ở thanh toán khác.", "PAYMENT_REFERENCE_DUPLICATE"
            ) from None
        return payment, entitlement

    async def revoke(self, user_id: str, admin_id: str, reason: str):
        await self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        rows = list(
            await self.db.scalars(
                select(UserEntitlement)
                .where(
                    UserEntitlement.user_id == user_id,
                    UserEntitlement.status == "ACTIVE",
                    UserEntitlement.expires_at > utcnow(),
                )
                .with_for_update()
            )
        )
        for row in rows:
            row.status = "REVOKED"
        self.db.add(
            AdminAuditLog(
                admin_user_id=admin_id,
                action="REVOKE_VIP",
                target_type="USER",
                target_id=user_id,
                details={"reason": reason, "count": len(rows)},
            )
        )
        await self.db.commit()
        return len(rows)
