from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.db.base import utcnow
from app.models import User
from app.models.commerce import Payment, ProductEvent, SubscriptionPlan, UserEntitlement
from app.schemas.commerce import CheckoutCreate, ProductEventCreate, ProfileUpdate
from app.services.commerce import CommerceService, entitlement_view, payment_view, plan_view
from app.services.entitlements import EntitlementService

router = APIRouter(tags=["Subscriptions"])


@router.get("/subscription/plans")
async def plans(db: DB):
    rows = await db.scalars(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.sort_order)
    )
    return {"items": [plan_view(row) for row in rows], "currency": "VND"}


@router.get("/subscription/me")
async def my_subscription(db: DB, user: CurrentUser):
    rows = list(
        await db.scalars(
            select(UserEntitlement)
            .where(UserEntitlement.user_id == user.id)
            .order_by(UserEntitlement.created_at.desc())
            .limit(100)
        )
    )
    access = await EntitlementService(db).summary(user)
    current = next((r for r in rows if r.status == "ACTIVE" and r.starts_at <= utcnow() < r.expires_at), None)
    current_plan = await db.get(SubscriptionPlan, current.plan_id) if current and current.plan_id else None
    return {
        "access": access,
        "current": entitlement_view(current) if current else None,
        "current_plan": plan_view(current_plan) if current_plan else None,
        "history": [entitlement_view(r) for r in rows],
        "server_now": utcnow(),
    }


@router.get("/entitlements/me")
async def my_entitlements(db: DB, user: CurrentUser):
    return await EntitlementService(db).summary(user)


@router.post("/payments", status_code=201)
async def checkout(data: CheckoutCreate, db: DB, user: CurrentUser):
    payment = await CommerceService(db).create_pending(user.id, data.plan_code)
    return {
        "payment": payment_view(payment),
        "instructions_vi": "Thanh toán đang chờ xác nhận thủ công. Liên hệ hỗ trợ để được hướng dẫn chuyển khoản. VIP chỉ kích hoạt sau khi quản trị viên xác nhận.",
    }


@router.get("/payments/me")
async def my_payments(db: DB, user: CurrentUser):
    rows = await db.scalars(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(100)
    )
    return {"items": [payment_view(row) for row in rows]}


@router.get("/account/profile")
async def profile(db: DB, user: CurrentUser):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "joined_at": user.created_at,
        "learning_goal": user.learning_goal,
        "access": await EntitlementService(db).summary(user),
    }


@router.patch("/account/profile")
async def update_profile(data: ProfileUpdate, db: DB, user: CurrentUser):
    user.name = data.name.strip() if data.name else None
    user.learning_goal = data.learning_goal.strip() if data.learning_goal else None
    await db.commit()
    return await profile(db, user)


@router.post("/events", status_code=202)
async def event(data: ProductEventCreate, db: DB, user: CurrentUser):
    await db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    today = utcnow().astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    existing = await db.scalar(
        select(ProductEvent.id)
        .where(
            ProductEvent.user_id == user.id, ProductEvent.name == data.name, ProductEvent.created_at >= start
        )
        .limit(1)
    )
    if not existing:
        db.add(ProductEvent(user_id=user.id, name=data.name, details={}))
        await db.commit()
    return {"accepted": True}
