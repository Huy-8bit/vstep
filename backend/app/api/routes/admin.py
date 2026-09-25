"""Management API. All endpoints use a role dependency, never an email allowlist."""

import hashlib
import secrets
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from sqlalchemy import exists, func, literal, or_, select, union_all
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.api.deps import DB, CurrentAdmin
from app.common.errors import AppError
from app.core.config import settings
from app.core.security import password_hasher
from app.db.base import utcnow
from app.models import AIUsageLog, ExamSession, User, WritingAttempt, WritingQuestion
from app.models.commerce import (
    AdminAuditLog,
    Payment,
    ProductEvent,
    SubscriptionPlan,
    TrialUsage,
    UserEntitlement,
)
from app.models.library import LibraryQuestion
from app.models.reading import ReadingExamSession, ReadingPassage, ReadingQuestion
from app.models.speaking import SpeakingAnswer, SpeakingExamSession, SpeakingQuestion
from app.repositories.library import QuestionRepository
from app.schemas.commerce import (
    AdminQuestionEdit,
    CheckoutCreate,
    GrantVip,
    ManualConfirm,
    PlanUpdate,
    QuestionPublication,
    ReadingKeyUpdate,
    RevokeVip,
    TestFlagUpdate,
    TestUserCreate,
    UserStatusUpdate,
)
from app.schemas.library import practice_issues
from app.services.ai_cost_service import AICostService
from app.services.commerce import CommerceService, entitlement_view, payment_view, plan_view
from app.services.entitlements import EntitlementService
from app.services.library_practice_service import LibraryPracticeService

router = APIRouter(prefix="/admin", tags=["Admin"])
TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def business_start(days=0):
    local = utcnow().astimezone(TZ)
    return datetime.combine(local.date() - timedelta(days=days), time.min, tzinfo=TZ)


def real_users():
    return User.role == "USER", User.is_test_account.is_(False)


def model_for(skill):
    return {"writing": WritingQuestion, "speaking": SpeakingQuestion, "reading": ReadingPassage}.get(skill)


def question_view(skill, row):
    return {
        "id": row.id,
        "skill": skill,
        "title": getattr(row, "title", None)
        or getattr(row, "instruction", None)
        or getattr(row, "question_text", ""),
        "part": getattr(row, "task_type", None)
        or getattr(row, "part", None)
        or ("passage" if skill == "reading" else None),
        "topic": row.topic,
        "source": "IMPORTED"
        if (row.generation_diagnostics or {}).get("origin") == "ADMIN_IMPORT"
        else row.source,
        "access_tier": row.access_tier,
        "is_published": row.is_published,
        "available_for_free_trial": row.available_for_free_trial,
        "is_featured": row.is_featured,
        "quality_valid": bool((row.generation_diagnostics or {}).get("quality_valid")),
        "question_type": getattr(row, "question_type", None),
        "created_at": row.created_at,
        "library_question_id": row.library_question_id,
    }


async def user_row(db, user_id: str, *, lock=False):
    query = select(User).where(User.id == user_id)
    if lock:
        query = query.with_for_update()
    row = await db.scalar(query)
    if not row:
        raise AppError(404, "Không tìm thấy người dùng.")
    return row


@router.get("/dashboard")
async def dashboard(db: DB, admin: CurrentAdmin):
    now = utcnow()
    today, week, month = business_start(), business_start(6), business_start(29)
    total = await db.scalar(select(func.count(User.id)).where(*real_users())) or 0
    registered_today = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.created_at >= today)) or 0
    )
    registered_week = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.created_at >= week)) or 0
    )
    registered_month = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.created_at >= month)) or 0
    )
    active_day = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.last_login_at >= today)) or 0
    )
    active_week = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.last_login_at >= week)) or 0
    )
    active_month = (
        await db.scalar(select(func.count(User.id)).where(*real_users(), User.last_login_at >= month)) or 0
    )
    vip_end = (
        select(UserEntitlement.user_id, func.max(UserEntitlement.expires_at).label("effective_expiry"))
        .join(User, User.id == UserEntitlement.user_id)
        .where(*real_users(), UserEntitlement.status == "ACTIVE", UserEntitlement.expires_at > now)
        .group_by(UserEntitlement.user_id)
        .having(func.min(UserEntitlement.starts_at) <= now)
        .subquery()
    )
    vip = await db.scalar(select(func.count()).select_from(vip_end)) or 0
    paid_vip = (
        await db.scalar(
            select(func.count(func.distinct(UserEntitlement.user_id))).where(
                UserEntitlement.user_id.in_(select(vip_end.c.user_id)),
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.source == "PURCHASE",
                UserEntitlement.expires_at > now,
            )
        )
        or 0
    )
    granted_vip = max(0, vip - paid_vip)
    expiry = {}
    for label, interval in (
        ("24h", timedelta(hours=24)),
        ("3d", timedelta(days=3)),
        ("7d", timedelta(days=7)),
    ):
        expiry[label] = (
            await db.scalar(
                select(func.count()).select_from(vip_end).where(vip_end.c.effective_expiry < now + interval)
            )
            or 0
        )
    paid_query = (
        select(Payment).join(User, User.id == Payment.user_id).where(*real_users(), Payment.status == "PAID")
    )

    async def revenue(since=None):
        query = (
            select(func.coalesce(func.sum(Payment.amount_vnd), 0))
            .select_from(Payment)
            .join(User)
            .where(*real_users(), Payment.status == "PAID")
        )
        if since:
            query = query.where(Payment.paid_at >= since)
        return int(await db.scalar(query) or 0)

    purchases = await db.scalar(select(func.count()).select_from(paid_query.subquery())) or 0
    converted = (
        await db.scalar(
            select(func.count(func.distinct(Payment.user_id)))
            .join(User)
            .where(
                *real_users(),
                Payment.status == "PAID",
                Payment.user_id.in_(select(TrialUsage.user_id).where(TrialUsage.used_count > 0)),
            )
        )
        or 0
    )
    ai_filter = (
        AIUsageLog.category.not_in(["evaluation", "shadow", "legacy"]),
        User.role == "USER",
        User.is_test_account.is_(False),
    )

    async def ai_cost(since):
        value = await db.scalar(
            select(func.sum(AIUsageLog.estimated_cost_usd))
            .join(User, AIUsageLog.user_id == User.id)
            .where(*ai_filter, AIUsageLog.created_at >= since)
        )
        return float(value) if value is not None else 0.0

    trial_users = (
        await db.scalar(
            select(func.count(func.distinct(TrialUsage.user_id)))
            .join(User)
            .where(*real_users(), TrialUsage.used_count > 0)
        )
        or 0
    )
    first_practice_ids = (
        select(ExamSession.user_id)
        .where(ExamSession.status == "SUBMITTED")
        .union(
            select(SpeakingExamSession.user_id).where(SpeakingExamSession.status == "COMPLETED"),
            select(ReadingExamSession.user_id).where(ReadingExamSession.status == "SUBMITTED"),
        )
        .subquery()
    )
    first_practice = (
        await db.scalar(
            select(func.count(func.distinct(first_practice_ids.c.user_id)))
            .select_from(first_practice_ids)
            .join(User, User.id == first_practice_ids.c.user_id)
            .where(*real_users())
        )
        or 0
    )
    return {
        "total_users": total,
        "new_users_today": registered_today,
        "new_users_week": registered_week,
        "new_users_month": registered_month,
        "active_users_today": active_day,
        "active_users_week": active_week,
        "active_users_month": active_month,
        "free_users": max(0, total - vip),
        "vip_users": vip,
        "paid_vip_users": paid_vip,
        "admin_granted_vip_users": granted_vip,
        "vip_expiring": expiry,
        "total_vip_purchases": purchases,
        "revenue_today_vnd": await revenue(today),
        "revenue_month_vnd": await revenue(
            datetime.combine(now.astimezone(TZ).date().replace(day=1), time.min, tzinfo=TZ)
        ),
        "revenue_30d_vnd": await revenue(month),
        "total_revenue_vnd": await revenue(),
        "ai_cost_today_usd": await ai_cost(today),
        "ai_cost_month_usd": await ai_cost(
            datetime.combine(now.astimezone(TZ).date().replace(day=1), time.min, tzinfo=TZ)
        ),
        "ai_cost_30d_usd": await ai_cost(month),
        "trial_users": trial_users,
        "completed_first_practice": first_practice,
        "converted_users": converted,
        "vip_conversion_rate": round(converted / trial_users * 100, 1) if trial_users else None,
        "server_now": now,
        "definitions": {
            "active_user": "Đăng nhập trong khoảng đo",
            "revenue": "Chỉ giao dịch PAID của người dùng thật",
            "ai_cost_currency": "USD",
        },
    }


@router.get("/dashboard/series")
async def dashboard_series(db: DB, admin: CurrentAdmin, days: int = Query(30, ge=7, le=90)):
    """Daily local-business-date points; zero days are explicit, never invented trends."""
    start = business_start(days - 1)
    registration_day = func.date(func.timezone("Asia/Ho_Chi_Minh", User.created_at))
    payment_day = func.date(func.timezone("Asia/Ho_Chi_Minh", Payment.paid_at))
    users = dict(
        (
            await db.execute(
                select(registration_day, func.count(User.id))
                .where(*real_users(), User.created_at >= start)
                .group_by(registration_day)
            )
        ).all()
    )
    revenue = dict(
        (
            await db.execute(
                select(payment_day, func.coalesce(func.sum(Payment.amount_vnd), 0))
                .join(User, User.id == Payment.user_id)
                .where(*real_users(), Payment.status == "PAID", Payment.paid_at >= start)
                .group_by(payment_day)
            )
        ).all()
    )
    today = utcnow().astimezone(TZ).date()
    return {
        "items": [
            {
                "day": (day := today - timedelta(days=index)).isoformat(),
                "users": int(users.get(day, 0)),
                "revenue_vnd": int(revenue.get(day, 0)),
            }
            for index in range(days - 1, -1, -1)
        ]
    }


@router.get("/dashboard/operations")
async def dashboard_operations(db: DB, admin: CurrentAdmin):
    now = utcnow()
    payments = (
        await db.execute(
            select(Payment, User.email)
            .join(User)
            .where(*real_users())
            .order_by(Payment.created_at.desc())
            .limit(5)
        )
    ).all()
    users = list(
        await db.scalars(select(User).where(*real_users()).order_by(User.created_at.desc()).limit(5))
    )
    latest_vip_expiry = (
        select(
            UserEntitlement.user_id,
            func.max(UserEntitlement.expires_at).label("expires_at"),
        )
        .where(UserEntitlement.status == "ACTIVE", UserEntitlement.expires_at > now)
        .group_by(UserEntitlement.user_id)
        .subquery()
    )
    expiry = (
        await db.execute(
            select(UserEntitlement, User.email)
            .join(User, User.id == UserEntitlement.user_id)
            .join(
                latest_vip_expiry,
                (latest_vip_expiry.c.user_id == UserEntitlement.user_id)
                & (latest_vip_expiry.c.expires_at == UserEntitlement.expires_at),
            )
            .where(
                *real_users(),
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.starts_at <= now,
                UserEntitlement.expires_at > now,
                UserEntitlement.expires_at < now + timedelta(days=7),
            )
            .order_by(UserEntitlement.expires_at)
            .limit(5)
        )
    ).all()
    costs = (
        await db.execute(
            select(User.id, User.email, func.sum(AIUsageLog.estimated_cost_usd).label("cost"))
            .join(AIUsageLog, AIUsageLog.user_id == User.id)
            .where(
                *real_users(),
                AIUsageLog.created_at >= business_start(29),
                AIUsageLog.category.not_in(["evaluation", "shadow", "legacy"]),
            )
            .group_by(User.id)
            .order_by(func.sum(AIUsageLog.estimated_cost_usd).desc().nullslast())
            .limit(5)
        )
    ).all()
    pending_old = (
        await db.scalar(
            select(func.count(Payment.id))
            .join(User)
            .where(*real_users(), Payment.status == "PENDING", Payment.created_at < now - timedelta(hours=1))
        )
        or 0
    )
    drafts = 0
    for model in (WritingQuestion, SpeakingQuestion, ReadingPassage):
        drafts += (
            await db.scalar(
                select(func.count(model.id)).where(
                    model.owner_id.is_(None), model.is_published.is_(False), model.access_tier != "INTERNAL"
                )
            )
            or 0
        )
    return {
        "recent_payments": [{**payment_view(payment), "email": email} for payment, email in payments],
        "recent_users": [
            {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at}
            for user in users
        ],
        "expiring_vip": [{**entitlement_view(row), "email": email} for row, email in expiry],
        "high_cost_users": [
            {"id": uid, "email": email, "cost_usd": float(cost) if cost is not None else None}
            for uid, email, cost in costs
        ],
        "attention": {"pending_payments_over_1h": pending_old, "question_drafts": drafts},
        "server_now": now,
    }


@router.get("/users")
async def users(
    db: DB,
    admin: CurrentAdmin,
    search: str = Query("", max_length=200),
    status: str = Query("all", pattern=r"^(all|ACTIVE|DISABLED)$"),
    access: str = Query("all", pattern=r"^(all|VIP|FREE)$"),
    plan: str = Query("all", max_length=30),
    test: str = Query("all", pattern=r"^(all|yes|no)$"),
    registered_after: datetime | None = None,
    last_active_after: datetime | None = None,
    sort: str = Query(
        "registered_desc", pattern=r"^(registered_desc|registered_asc|last_active_desc|ai_cost_desc)$"
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
):
    query = select(User)
    now = utcnow()
    vip = exists(
        select(UserEntitlement.id).where(
            UserEntitlement.user_id == User.id,
            UserEntitlement.status == "ACTIVE",
            UserEntitlement.starts_at <= now,
            UserEntitlement.expires_at > now,
        )
    )
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(or_(User.email.ilike(f"%{escaped}%"), User.name.ilike(f"%{escaped}%")))
    if status != "all":
        query = query.where(User.status == status)
    if access != "all":
        query = query.where(
            or_(User.role == "ADMIN", vip) if access == "VIP" else (User.role != "ADMIN") & ~vip
        )
    if test != "all":
        query = query.where(User.is_test_account.is_(test == "yes"))
    if plan != "all":
        query = query.where(
            exists(
                select(UserEntitlement.id)
                .join(SubscriptionPlan)
                .where(
                    UserEntitlement.user_id == User.id,
                    UserEntitlement.status == "ACTIVE",
                    UserEntitlement.starts_at <= now,
                    UserEntitlement.expires_at > now,
                    SubscriptionPlan.code == plan,
                )
            )
        )
    if registered_after:
        query = query.where(User.created_at >= registered_after)
    if last_active_after:
        query = query.where(User.last_login_at >= last_active_after)
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    if sort == "ai_cost_desc":
        cost = (
            select(AIUsageLog.user_id, func.sum(AIUsageLog.estimated_cost_usd).label("cost"))
            .group_by(AIUsageLog.user_id)
            .subquery()
        )
        query = query.outerjoin(cost, cost.c.user_id == User.id).order_by(
            cost.c.cost.desc().nullslast(), User.created_at.desc()
        )
    else:
        query = query.order_by(
            {
                "registered_desc": User.created_at.desc(),
                "registered_asc": User.created_at.asc(),
                "last_active_desc": User.last_login_at.desc().nullslast(),
            }[sort],
            User.id,
        )
    rows = list(await db.scalars(query.offset(offset).limit(limit)))
    return {"total": total, "items": [await admin_user_view(db, row) for row in rows]}


async def admin_user_view(db, row: User):
    access = await EntitlementService(db).summary(row)
    trial = list(await db.scalars(select(TrialUsage).where(TrialUsage.user_id == row.id)))
    attempts = {
        "writing": await db.scalar(
            select(func.count()).select_from(WritingAttempt).where(WritingAttempt.user_id == row.id)
        )
        or 0,
        "speaking": await db.scalar(
            select(func.count()).select_from(SpeakingExamSession).where(SpeakingExamSession.user_id == row.id)
        )
        or 0,
        "reading": await db.scalar(
            select(func.count()).select_from(ReadingExamSession).where(ReadingExamSession.user_id == row.id)
        )
        or 0,
    }
    cost = await db.scalar(
        select(func.sum(AIUsageLog.estimated_cost_usd)).where(
            AIUsageLog.user_id == row.id, AIUsageLog.category.not_in(["evaluation", "shadow"])
        )
    )
    current = await db.scalar(
        select(UserEntitlement)
        .where(
            UserEntitlement.user_id == row.id,
            UserEntitlement.status == "ACTIVE",
            UserEntitlement.starts_at <= utcnow(),
            UserEntitlement.expires_at > utcnow(),
        )
        .order_by(UserEntitlement.expires_at.desc())
        .limit(1)
    )
    plan = await db.get(SubscriptionPlan, current.plan_id) if current and current.plan_id else None
    return {
        "id": row.id,
        "email": row.email,
        "name": row.name,
        "registered_at": row.created_at,
        "last_active": row.last_login_at,
        "role": row.role,
        "status": row.status,
        "is_test_account": row.is_test_account,
        "trial_used": {t.feature_code: t.used_count for t in trial},
        "access": access,
        "vip_start": current.starts_at if current else None,
        "vip_expiry": access["vip_expires_at"],
        "plan": plan_view(plan) if plan else None,
        "total_attempts": sum(attempts.values()),
        "attempts": attempts,
        "total_ai_cost_usd": float(cost) if cost is not None else None,
    }


@router.get("/users/{user_id}")
async def user_detail(user_id: str, db: DB, admin: CurrentAdmin):
    row = await user_row(db, user_id)
    entitlements = list(
        await db.scalars(
            select(UserEntitlement)
            .where(UserEntitlement.user_id == row.id)
            .order_by(UserEntitlement.created_at.desc())
        )
    )
    payments = list(
        await db.scalars(select(Payment).where(Payment.user_id == row.id).order_by(Payment.created_at.desc()))
    )
    return {
        **await admin_user_view(db, row),
        "entitlements": [entitlement_view(item) for item in entitlements],
        "payments": [payment_view(item) for item in payments],
        "learning_activity_count": await db.scalar(
            select(func.count()).select_from(ProductEvent).where(ProductEvent.user_id == row.id)
        )
        or 0,
        "server_now": utcnow(),
    }


@router.post("/users/{user_id}/grant-vip")
async def grant_vip(user_id: str, data: GrantVip, db: DB, admin: CurrentAdmin):
    row = await CommerceService(db).grant(user_id, data.duration_days, "ADMIN_GRANT", admin.id, data.reason)
    await db.commit()
    return entitlement_view(row)


@router.post("/users/{user_id}/revoke-vip")
async def revoke_vip(user_id: str, data: RevokeVip, db: DB, admin: CurrentAdmin):
    count = await CommerceService(db).revoke(user_id, admin.id, data.reason)
    return {"revoked": count}


@router.patch("/users/{user_id}/status")
async def change_status(user_id: str, data: UserStatusUpdate, db: DB, admin: CurrentAdmin):
    row = await user_row(db, user_id, lock=True)
    if row.id == admin.id and data.status == "DISABLED":
        raise AppError(409, "Không thể tự vô hiệu hóa tài khoản quản trị đang dùng.")
    row.status = data.status
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="DISABLE_USER" if data.status == "DISABLED" else "ENABLE_USER",
            target_type="USER",
            target_id=row.id,
            details={},
        )
    )
    await db.commit()
    return await admin_user_view(db, row)


@router.patch("/users/{user_id}/test-account")
async def set_test_account(user_id: str, data: TestFlagUpdate, db: DB, admin: CurrentAdmin):
    row = await user_row(db, user_id, lock=True)
    row.is_test_account = data.is_test_account
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="MARK_TEST_ACCOUNT",
            target_type="USER",
            target_id=row.id,
            details={"is_test_account": data.is_test_account},
        )
    )
    await db.commit()
    return await admin_user_view(db, row)


@router.post("/users/test-vip", status_code=201)
async def create_test_vip(data: TestUserCreate, db: DB, admin: CurrentAdmin):
    password = data.password or secrets.token_urlsafe(18)
    row = User(
        email=str(data.email).lower(),
        password_hash=await run_in_threadpool(password_hasher.hash, password),
        name=data.name,
        role="USER",
        status="ACTIVE",
        is_test_account=True,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise AppError(409, "Email này đã được đăng ký.") from None
    entitlement = await CommerceService(db).grant(
        row.id, data.duration_days, "ADMIN_GRANT", admin.id, "Test VIP user"
    )
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="CREATE_TEST_USER",
            target_type="USER",
            target_id=row.id,
            details={"days": data.duration_days},
        )
    )
    await db.commit()
    return {
        "user": await admin_user_view(db, row),
        "entitlement": entitlement_view(entitlement),
        "generated_password": password if data.password is None else None,
    }


@router.get("/subscriptions")
async def subscriptions(
    db: DB,
    admin: CurrentAdmin,
    state: str = Query("all", pattern=r"^(all|active|expiring|expired|manual|purchased)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    now = utcnow()
    query = (
        select(UserEntitlement, User.email, SubscriptionPlan.name)
        .join(User, User.id == UserEntitlement.user_id)
        .outerjoin(SubscriptionPlan, SubscriptionPlan.id == UserEntitlement.plan_id)
    )
    if state == "active":
        query = query.where(
            UserEntitlement.status == "ACTIVE",
            UserEntitlement.starts_at <= now,
            UserEntitlement.expires_at > now,
        )
    elif state == "expiring":
        query = query.where(
            UserEntitlement.status == "ACTIVE",
            UserEntitlement.starts_at <= now,
            UserEntitlement.expires_at.between(now, now + timedelta(days=7)),
        )
    elif state == "expired":
        query = query.where(UserEntitlement.expires_at <= now)
    elif state == "manual":
        query = query.where(UserEntitlement.source != "PURCHASE")
    elif state == "purchased":
        query = query.where(UserEntitlement.source == "PURCHASE")
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = (
        await db.execute(query.order_by(UserEntitlement.created_at.desc()).offset(offset).limit(limit))
    ).all()
    return {
        "total": total,
        "items": [
            {
                **entitlement_view(row),
                "email": email,
                "plan_name": plan_name,
                "remaining_seconds": max(0, int((row.expires_at - now).total_seconds()))
                if row.status == "ACTIVE"
                else 0,
            }
            for row, email, plan_name in rows
        ],
    }


@router.get("/payments")
async def payments(
    db: DB,
    admin: CurrentAdmin,
    status: str = Query("all", pattern=r"^(all|PENDING|PAID|FAILED|CANCELLED|EXPIRED|REFUNDED)$"),
    search: str = Query("", max_length=200),
    sort: str = Query("created_desc", pattern=r"^(created_desc|amount_desc|paid_desc)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Payment, User.email).join(User, User.id == Payment.user_id)
    if status != "all":
        query = query.where(Payment.status == status)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(User.email.ilike(f"%{escaped}%"), Payment.provider_payment_id.ilike(f"%{escaped}%"))
        )
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    order = {
        "created_desc": Payment.created_at.desc(),
        "amount_desc": Payment.amount_vnd.desc(),
        "paid_desc": Payment.paid_at.desc().nullslast(),
    }[sort]
    rows = (await db.execute(query.order_by(order, Payment.id).offset(offset).limit(limit))).all()
    return {"total": total, "items": [{**payment_view(payment), "email": email} for payment, email in rows]}


@router.get("/payments/summary")
async def payment_summary(db: DB, admin: CurrentAdmin):
    async def sum_paid(since):
        return int(
            await db.scalar(
                select(func.coalesce(func.sum(Payment.amount_vnd), 0))
                .join(User)
                .where(*real_users(), Payment.status == "PAID", Payment.paid_at >= since)
            )
            or 0
        )

    successful = (
        await db.scalar(
            select(func.count(Payment.id)).join(User).where(*real_users(), Payment.status == "PAID")
        )
        or 0
    )
    pending = (
        await db.scalar(
            select(func.count(Payment.id)).join(User).where(*real_users(), Payment.status == "PENDING")
        )
        or 0
    )
    return {
        "revenue_today_vnd": await sum_paid(business_start()),
        "revenue_7d_vnd": await sum_paid(business_start(6)),
        "revenue_30d_vnd": await sum_paid(business_start(29)),
        "successful_payments": successful,
        "pending_payments": pending,
    }


@router.get("/payments/{payment_id}")
async def payment_detail(payment_id: str, db: DB, admin: CurrentAdmin):
    row = await db.scalar(select(Payment).where(Payment.id == payment_id))
    if not row:
        raise AppError(404, "Không tìm thấy thanh toán.")
    user = await db.get(User, row.user_id)
    entitlement = await db.scalar(select(UserEntitlement).where(UserEntitlement.payment_id == row.id))
    return {
        **payment_view(row),
        "email": user.email if user else None,
        "entitlement": entitlement_view(entitlement) if entitlement else None,
    }


@router.post("/users/{user_id}/manual-payment", status_code=201)
async def create_manual_payment(user_id: str, data: CheckoutCreate, db: DB, admin: CurrentAdmin):
    await user_row(db, user_id)
    row = await CommerceService(db).create_pending(user_id, data.plan_code, admin.id)
    return payment_view(row)


@router.post("/payments/{payment_id}/confirm")
async def confirm_manual_payment(payment_id: str, data: ManualConfirm, db: DB, admin: CurrentAdmin):
    payment, entitlement = await CommerceService(db).confirm_manual(
        payment_id, admin.id, data.reference, data.reason
    )
    return {"payment": payment_view(payment), "entitlement": entitlement_view(entitlement)}


@router.get("/plans")
async def admin_plans(db: DB, admin: CurrentAdmin):
    rows = list(await db.scalars(select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order)))
    now = utcnow()
    items = []
    for row in rows:
        active_users = (
            await db.scalar(
                select(func.count(func.distinct(UserEntitlement.user_id)))
                .join(User, User.id == UserEntitlement.user_id)
                .where(
                    *real_users(),
                    UserEntitlement.plan_id == row.id,
                    UserEntitlement.status == "ACTIVE",
                    UserEntitlement.starts_at <= now,
                    UserEntitlement.expires_at > now,
                )
            )
            or 0
        )
        items.append({**plan_view(row), "active_users": active_users})
    return {"items": items}


@router.patch("/plans/{code}")
async def edit_plan(code: str, data: PlanUpdate, db: DB, admin: CurrentAdmin):
    row = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == code).with_for_update())
    if not row:
        raise AppError(404, "Không tìm thấy gói VIP.")
    changed = data.model_dump(exclude_unset=True)
    for key, value in changed.items():
        setattr(row, key, value)
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="EDIT_PLAN",
            target_type="PLAN",
            target_id=row.id,
            details={"changed": changed},
        )
    )
    await db.commit()
    return plan_view(row)


@router.get("/questions")
async def questions(
    db: DB,
    admin: CurrentAdmin,
    skill: str = Query("all", pattern=r"^(all|writing|speaking|reading)$"),
    publication: str = Query("all", pattern=r"^(all|published|draft|archived)$"),
    search: str = Query("", max_length=200),
    source: str = Query("all", pattern=r"^(all|SEED|AI|CUSTOM|IMPORTED)$"),
    access_tier: str = Query("all", pattern=r"^(all|FREE_TRIAL|VIP|INTERNAL)$"),
    topic: str = Query("", max_length=50),
    part: str = Query("all", pattern=r"^(all|1|2|3)$"),
    sort: str = Query("created_desc", pattern=r"^(created_desc|created_asc|attempts_desc)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
):
    selects = []
    for name in [skill] if skill != "all" else ["writing", "speaking", "reading"]:
        model = model_for(name)
        if name == "writing":
            attempt_count = (
                select(func.count(WritingAttempt.id))
                .where(WritingAttempt.question_id == model.id)
                .correlate(model)
                .scalar_subquery()
            )
        elif name == "speaking":
            attempt_count = (
                select(func.count(func.distinct(SpeakingAnswer.session_id)))
                .where(SpeakingAnswer.question_id == model.id)
                .correlate(model)
                .scalar_subquery()
            )
        else:
            attempt_count = (
                select(func.count(ReadingExamSession.id))
                .where(ReadingExamSession.passage_ids.contains(func.jsonb_build_array(model.id)))
                .correlate(model)
                .scalar_subquery()
            )
        query = select(
            literal(name).label("skill"),
            model.id.label("id"),
            model.created_at.label("created_at"),
            attempt_count.label("attempts"),
        ).where(model.owner_id.is_(None))
        if publication == "published":
            query = query.where(model.is_published.is_(True))
        elif publication == "draft":
            query = query.where(model.is_published.is_(False), model.access_tier != "INTERNAL")
        elif publication == "archived":
            query = query.where(model.access_tier == "INTERNAL")
        if source == "IMPORTED":
            query = query.where(model.generation_diagnostics["origin"].as_string() == "ADMIN_IMPORT")
        elif source == "CUSTOM":
            query = query.where(
                model.source == "CUSTOM",
                func.coalesce(model.generation_diagnostics["origin"].as_string(), "") != "ADMIN_IMPORT",
            )
        elif source != "all":
            query = query.where(model.source == source)
        if access_tier != "all":
            query = query.where(model.access_tier == access_tier)
        if topic:
            query = query.where(model.topic == topic)
        if part != "all" and name != "reading":
            query = query.where((model.task_type if name == "writing" else model.part) == int(part))
        elif part != "all" and name == "reading":
            continue
        if search:
            column = (
                model.title
                if name == "reading"
                else model.instruction
                if name == "writing"
                else model.question_text
            )
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(column.ilike(f"%{escaped}%"))
        selects.append(query)
    if not selects:
        return {"total": 0, "items": []}
    catalog = union_all(*selects).subquery() if len(selects) > 1 else selects[0].subquery()
    total = await db.scalar(select(func.count()).select_from(catalog)) or 0
    ordering = (
        catalog.c.attempts.desc()
        if sort == "attempts_desc"
        else catalog.c.created_at.asc()
        if sort == "created_asc"
        else catalog.c.created_at.desc()
    )
    candidates = (
        await db.execute(
            select(catalog.c.skill, catalog.c.id, catalog.c.attempts)
            .order_by(ordering, catalog.c.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    result = []
    for name, identifier, attempts in candidates:
        row = await db.get(model_for(name), identifier)
        result.append({**question_view(name, row), "attempts": int(attempts or 0)})
    return {"total": total, "items": result}


@router.get("/questions/{skill}/{question_id}")
async def question_detail(skill: str, question_id: str, db: DB, admin: CurrentAdmin):
    model = model_for(skill)
    if not model:
        raise AppError(404, "Không tìm thấy kỹ năng.")
    row = await db.get(model, question_id)
    if not row or row.owner_id is not None:
        raise AppError(404, "Không tìm thấy đề chung.")
    result = question_view(skill, row)
    if skill == "writing":
        result["attempts"] = (
            await db.scalar(select(func.count(WritingAttempt.id)).where(WritingAttempt.question_id == row.id))
            or 0
        )
    elif skill == "speaking":
        result["attempts"] = (
            await db.scalar(
                select(func.count(func.distinct(SpeakingAnswer.session_id))).where(
                    SpeakingAnswer.question_id == row.id
                )
            )
            or 0
        )
    else:
        result["attempts"] = (
            await db.scalar(
                select(func.count(ReadingExamSession.id)).where(
                    ReadingExamSession.passage_ids.contains([row.id])
                )
            )
            or 0
        )
    result["content"] = {
        name: getattr(row, name)
        for name in (
            ("instruction", "stimulus", "response_instruction", "requirements", "minimum_words")
            if skill == "writing"
            else (
                "question_text",
                "topic_sets",
                "situation",
                "options",
                "suggested_ideas",
                "follow_up_questions",
            )
            if skill == "speaking"
            else ("content", "paragraphs", "word_count")
        )
    }
    if skill == "reading":
        result["questions"] = [
            {
                "id": q.id,
                "question_number": q.question_number,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "answer_key_source": q.answer_key_source,
                "explanation_vi": q.explanation_vi,
                "evidence": q.evidence,
            }
            for q in row.questions
        ]
    return result


@router.patch("/questions/{skill}/{question_id}")
async def update_question_publication(
    skill: str, question_id: str, data: QuestionPublication, db: DB, admin: CurrentAdmin
):
    model = model_for(skill)
    if not model:
        raise AppError(404, "Không tìm thấy kỹ năng.")
    row = await db.scalar(
        select(model).where(model.id == question_id, model.owner_id.is_(None)).with_for_update()
    )
    if not row:
        raise AppError(404, "Không tìm thấy đề chung.")
    changed = data.model_dump(exclude_unset=True)
    tier = changed.get("access_tier", row.access_tier)
    trial = changed.get("available_for_free_trial", row.available_for_free_trial)
    if (tier == "FREE_TRIAL" or trial) and not (
        (skill == "writing" and row.task_type == 1) or (skill == "speaking" and row.part == 1)
    ):
        raise AppError(422, "Pool miễn phí chỉ nhận Writing Task 1 hoặc Speaking Part 1.")
    if trial and tier != "FREE_TRIAL":
        raise AppError(422, "Đề trial phải thuộc tầng FREE_TRIAL.")
    if tier != "FREE_TRIAL":
        changed["available_for_free_trial"] = False
    if (
        changed.get("is_published")
        and row.source == "AI"
        and not (row.generation_diagnostics or {}).get("quality_valid")
    ):
        raise AppError(422, "Đề chưa qua kiểm tra chất lượng; chưa thể xuất bản.")
    for key, value in changed.items():
        setattr(row, key, value)
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="PUBLISH_QUESTION" if row.is_published else "UNPUBLISH_QUESTION",
            target_type=skill.upper(),
            target_id=row.id,
            details=changed,
        )
    )
    await db.commit()
    return question_view(skill, row)


@router.delete("/questions/{skill}/{question_id}")
async def archive_question(skill: str, question_id: str, db: DB, admin: CurrentAdmin):
    return await update_question_publication(
        skill,
        question_id,
        QuestionPublication(is_published=False, access_tier="INTERNAL", available_for_free_trial=False),
        db,
        admin,
    )


@router.patch("/questions/{skill}/{question_id}/content")
async def edit_question_content(
    skill: str, question_id: str, data: AdminQuestionEdit, db: DB, admin: CurrentAdmin
):
    model = model_for(skill)
    if not model:
        raise AppError(404, "Không tìm thấy kỹ năng.")
    row = await db.scalar(
        select(model).where(model.id == question_id, model.owner_id.is_(None)).with_for_update()
    )
    if not row:
        raise AppError(404, "Không tìm thấy đề chung.")
    if row.is_published:
        raise AppError(409, "Hãy hủy xuất bản trước khi sửa nội dung đề.", "QUESTION_PUBLISHED")
    changed = data.model_dump(exclude_unset=True)
    allowed = {"topic", "source"} | (
        {"instruction", "stimulus", "question_type"}
        if skill == "writing"
        else {"question_text", "question_type"}
        if skill == "speaking"
        else {"title"}
    )
    if set(changed) - allowed:
        raise AppError(422, "Trường nội dung không phù hợp với kỹ năng này.")
    for key, value in changed.items():
        setattr(row, key, value)
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="EDIT_QUESTION",
            target_type=skill.upper(),
            target_id=row.id,
            details={"fields": list(changed)},
        )
    )
    await db.commit()
    return question_view(skill, row)


@router.patch("/questions/reading/{passage_id}/keys/{key_id}")
async def edit_reading_key(passage_id: str, key_id: str, data: ReadingKeyUpdate, db: DB, admin: CurrentAdmin):
    passage = await db.scalar(
        select(ReadingPassage)
        .where(ReadingPassage.id == passage_id, ReadingPassage.owner_id.is_(None))
        .with_for_update()
    )
    if not passage:
        raise AppError(404, "Không tìm thấy bài đọc.")
    if passage.is_published:
        raise AppError(409, "Hãy hủy xuất bản trước khi sửa đáp án.", "QUESTION_PUBLISHED")
    key = await db.scalar(
        select(ReadingQuestion)
        .where(ReadingQuestion.id == key_id, ReadingQuestion.passage_id == passage.id)
        .with_for_update()
    )
    if not key:
        raise AppError(404, "Không tìm thấy câu hỏi.")
    key.correct_answer = data.correct_answer
    key.answer_key_source = data.answer_key_source
    if "explanation_vi" in data.model_fields_set:
        key.explanation_vi = data.explanation_vi
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="EDIT_ANSWER_KEY",
            target_type="READING_QUESTION",
            target_id=key.id,
            details={"passage_id": passage.id, "correct_answer": data.correct_answer},
        )
    )
    await db.commit()
    return {"id": key.id, **data.model_dump()}


@router.get("/question-drafts")
async def question_drafts(
    db: DB, admin: CurrentAdmin, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
):
    query = select(LibraryQuestion).where(
        LibraryQuestion.user_id == admin.id, LibraryQuestion.deleted_at.is_(None)
    )
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(
        await db.scalars(query.order_by(LibraryQuestion.updated_at.desc()).offset(offset).limit(limit))
    )
    items = []
    for row in rows:
        model = model_for(row.skill)
        imported = (
            await db.scalar(
                select(func.count(model.id)).where(
                    model.owner_id.is_(None),
                    model.library_question_id == row.id,
                    model.library_revision == row.revision,
                )
            )
            or 0
        )
        items.append(
            {
                "id": row.id,
                "title": row.title,
                "skill": row.skill,
                "part": row.part,
                "updated_at": row.updated_at,
                "imported_count": imported,
            }
        )
    return {"total": total, "items": items}


@router.post("/question-drafts/{draft_id}/to-bank", status_code=201)
async def add_draft_to_bank(draft_id: str, db: DB, admin: CurrentAdmin):
    """Reuse the existing editor, import parser and materializer; publish separately."""
    draft = await QuestionRepository(db, admin.id).get(draft_id, lock=True)
    doc = await QuestionRepository(db, admin.id).revision(draft, draft.revision)
    issues = practice_issues(doc)
    if issues:
        raise AppError(422, " ".join(issues), "QUESTION_INCOMPLETE")
    model = model_for(doc.skill)
    existing = list(
        await db.scalars(
            select(model).where(
                model.owner_id.is_(None),
                model.library_question_id == draft.id,
                model.library_revision == draft.revision,
            )
        )
    )
    if existing:
        return {"items": [question_view(doc.skill, row) for row in existing], "already_imported": True}
    rows = LibraryPracticeService.materialize(draft, draft.revision, doc)
    for row in rows:
        row.owner_id = None
        row.is_published = False
        row.access_tier = "VIP"
        row.available_for_free_trial = False
        row.fingerprint = hashlib.sha256(f"global:{row.fingerprint}".encode()).hexdigest()
        row.generation_diagnostics = {"origin": "ADMIN_IMPORT", "quality_valid": True}
    db.add_all(rows)
    await db.flush()
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action="IMPORT_QUESTION",
            target_type="LIBRARY_QUESTION",
            target_id=draft.id,
            details={"revision": draft.revision, "skill": doc.skill, "count": len(rows)},
        )
    )
    await db.commit()
    return {"items": [question_view(doc.skill, row) for row in rows], "already_imported": False}


@router.get("/exam-sets")
async def exam_sets(
    db: DB,
    admin: CurrentAdmin,
    search: str = "",
    skill: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    filters = [
        LibraryQuestion.user_id == admin.id,
        LibraryQuestion.part == "full",
        LibraryQuestion.deleted_at.is_(None),
    ]
    if search.strip():
        filters.append(LibraryQuestion.title.ilike(f"%{search.strip()}%"))
    if skill in {"writing", "speaking", "reading"}:
        filters.append(LibraryQuestion.skill == skill)
    total = await db.scalar(select(func.count()).select_from(LibraryQuestion).where(*filters)) or 0
    rows = list(
        await db.scalars(
            select(LibraryQuestion)
            .where(*filters)
            .order_by(LibraryQuestion.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    items = []
    for row in rows:
        model = model_for(row.skill)
        bank_count = (
            await db.scalar(
                select(func.count())
                .select_from(model)
                .where(
                    model.owner_id.is_(None),
                    model.library_question_id == row.id,
                    model.library_revision == row.revision,
                )
            )
            or 0
        )
        items.append(
            {
                "id": row.id,
                "title": row.title,
                "skill": row.skill,
                "revision": row.revision,
                "bank_question_count": bank_count,
                "created_at": row.created_at,
            }
        )
    return {"items": items, "total": total}


@router.get("/ai-usage")
async def ai_usage(db: DB, admin: CurrentAdmin, days: int = Query(30, ge=1, le=90)):
    overview = await AICostService(db).overview(days)
    since = business_start(days - 1)
    real_filter = (
        User.role == "USER",
        User.is_test_account.is_(False),
        AIUsageLog.category.not_in(["evaluation", "shadow", "legacy"]),
    )
    cost_today = await db.scalar(
        select(func.sum(AIUsageLog.estimated_cost_usd))
        .join(User)
        .where(*real_filter, AIUsageLog.created_at >= business_start())
    )
    cost_period = await db.scalar(
        select(func.sum(AIUsageLog.estimated_cost_usd))
        .join(User)
        .where(*real_filter, AIUsageLog.created_at >= since)
    )
    active = (
        await db.scalar(
            select(func.count(func.distinct(AIUsageLog.user_id)))
            .join(User)
            .where(*real_filter, AIUsageLog.created_at >= since)
        )
        or 0
    )
    paid_ids = select(UserEntitlement.user_id).where(
        UserEntitlement.status == "ACTIVE",
        UserEntitlement.source == "PURCHASE",
        UserEntitlement.starts_at <= utcnow(),
        UserEntitlement.expires_at > utcnow(),
    )
    paid_count = (
        await db.scalar(
            select(func.count(func.distinct(User.id))).where(*real_users(), User.id.in_(paid_ids))
        )
        or 0
    )
    paid_cost = await db.scalar(
        select(func.sum(AIUsageLog.estimated_cost_usd))
        .join(User)
        .where(*real_filter, AIUsageLog.created_at >= since, User.id.in_(paid_ids))
    )
    operation_rows = (
        await db.execute(
            select(
                AIUsageLog.operation,
                func.count(AIUsageLog.id),
                func.sum(AIUsageLog.estimated_cost_usd),
                func.count(AIUsageLog.id).filter(AIUsageLog.estimated_cost_usd.is_(None)),
            )
            .join(User)
            .where(*real_filter, AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.operation)
            .order_by(func.sum(AIUsageLog.estimated_cost_usd).desc().nullslast())
        )
    ).all()
    model_rows = (
        await db.execute(
            select(AIUsageLog.model, func.count(AIUsageLog.id), func.sum(AIUsageLog.estimated_cost_usd))
            .join(User)
            .where(*real_filter, AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.model)
            .order_by(func.sum(AIUsageLog.estimated_cost_usd).desc().nullslast())
        )
    ).all()
    rows = (
        await db.execute(
            select(
                User.id,
                User.email,
                User.last_login_at,
                func.sum(AIUsageLog.estimated_cost_usd),
                func.count(AIUsageLog.id),
            )
            .join(AIUsageLog, AIUsageLog.user_id == User.id)
            .where(
                AIUsageLog.created_at >= since, AIUsageLog.category.not_in(["evaluation", "shadow", "legacy"])
            )
            .group_by(User.id, User.email)
            .order_by(func.sum(AIUsageLog.estimated_cost_usd).desc().nullslast())
            .limit(30)
        )
    ).all()
    users = []
    for uid, email, last_login, cost, calls in rows:
        attempts = 0
        for model in (ExamSession, SpeakingExamSession, ReadingExamSession):
            attempts += await db.scalar(select(func.count(model.id)).where(model.user_id == uid)) or 0
        users.append(
            {
                "id": uid,
                "email": email,
                "last_active": last_login,
                "cost_usd": float(cost) if cost is not None else None,
                "calls": calls,
                "attempts": attempts,
                "tier": "VIP" if await EntitlementService(db).vip_expiry(uid) else "FREE",
            }
        )
    return {
        "overview": overview,
        "summary": {
            "cost_today_usd": float(cost_today or 0),
            "cost_period_usd": float(cost_period or 0),
            "cost_per_active_user_usd": float(cost_period or 0) / active if active else None,
            "cost_per_paid_user_usd": float(paid_cost or 0) / paid_count if paid_count else None,
            "active_users": active,
            "paid_users": paid_count,
        },
        "by_operation": [
            {
                "name": name,
                "calls": count,
                "cost_usd": float(cost) if cost is not None else None,
                "unknown_cost_calls": unknown,
            }
            for name, count, cost, unknown in operation_rows
        ],
        "by_model": [
            {"name": name, "calls": count, "cost_usd": float(cost) if cost is not None else None}
            for name, count, cost in model_rows
        ],
        "users": users,
    }


@router.get("/reports")
async def reports(db: DB, admin: CurrentAdmin):
    today = business_start()
    month = datetime.combine(today.date().replace(day=1), time.min, tzinfo=TZ)
    seven = business_start(6)
    thirty = business_start(29)
    paid = select(Payment).join(User).where(*real_users(), Payment.status == "PAID")
    revenue_by_plan = (
        await db.execute(
            select(
                SubscriptionPlan.code, func.count(Payment.id), func.coalesce(func.sum(Payment.amount_vnd), 0)
            )
            .join(Payment, Payment.plan_id == SubscriptionPlan.id)
            .join(User, User.id == Payment.user_id)
            .where(*real_users(), Payment.status == "PAID")
            .group_by(SubscriptionPlan.code)
        )
    ).all()
    trial_by_feature = (
        await db.execute(
            select(TrialUsage.feature_code, func.count(func.distinct(TrialUsage.user_id)))
            .join(User)
            .where(*real_users(), TrialUsage.used_count > 0)
            .group_by(TrialUsage.feature_code)
        )
    ).all()
    completed = {}
    for name, model in (
        ("writing", ExamSession),
        ("speaking", SpeakingExamSession),
        ("reading", ReadingExamSession),
    ):
        completed[name] = (
            await db.scalar(
                select(func.count(model.id))
                .join(User, User.id == model.user_id)
                .where(*real_users(), model.status == ("COMPLETED" if name == "speaking" else "SUBMITTED"))
            )
            or 0
        )
    purchases = await db.scalar(select(func.count()).select_from(paid.subquery())) or 0
    paid_users = (
        await db.scalar(
            select(func.count(func.distinct(Payment.user_id)))
            .join(User)
            .where(*real_users(), Payment.status == "PAID")
        )
        or 0
    )
    expired = (
        await db.scalar(
            select(func.count(func.distinct(UserEntitlement.user_id)))
            .join(User, User.id == UserEntitlement.user_id)
            .where(
                *real_users(),
                UserEntitlement.status == "ACTIVE",
                UserEntitlement.expires_at <= utcnow(),
                UserEntitlement.user_id.not_in(
                    select(UserEntitlement.user_id).where(
                        UserEntitlement.status == "ACTIVE", UserEntitlement.expires_at > utcnow()
                    )
                ),
            )
        )
        or 0
    )
    total = await db.scalar(select(func.count(User.id)).where(*real_users())) or 0
    revenue_month = (
        await db.scalar(
            select(func.coalesce(func.sum(Payment.amount_vnd), 0))
            .join(User)
            .where(*real_users(), Payment.status == "PAID", Payment.paid_at >= month)
        )
        or 0
    )

    async def revenue_since(since):
        return int(
            await db.scalar(
                select(func.coalesce(func.sum(Payment.amount_vnd), 0))
                .join(User)
                .where(*real_users(), Payment.status == "PAID", Payment.paid_at >= since)
            )
            or 0
        )

    async def event_users(name, *, trial_only=False):
        query = (
            select(func.count(func.distinct(ProductEvent.user_id)))
            .join(User, User.id == ProductEvent.user_id)
            .where(*real_users(), ProductEvent.name == name)
        )
        if trial_only:
            query = query.where(ProductEvent.details["access_source"].as_string() == "TRIAL")
        return await db.scalar(query) or 0

    trial_started = (
        await db.scalar(
            select(func.count(func.distinct(TrialUsage.user_id)))
            .join(User, User.id == TrialUsage.user_id)
            .where(*real_users(), TrialUsage.used_count > 0)
        )
        or 0
    )
    trial_completed = await event_users("PRACTICE_COMPLETED", trial_only=True)
    pricing_viewed = await event_users("PRICING_VIEWED")
    checkout_started = await event_users("CHECKOUT_STARTED")
    converted = (
        await db.scalar(
            select(func.count(func.distinct(Payment.user_id)))
            .join(User, User.id == Payment.user_id)
            .where(
                *real_users(),
                Payment.status == "PAID",
                Payment.user_id.in_(select(TrialUsage.user_id).where(TrialUsage.used_count > 0)),
            )
        )
        or 0
    )
    full_exams = {}
    for name, model in (
        ("writing", ExamSession),
        ("speaking", SpeakingExamSession),
        ("reading", ReadingExamSession),
    ):
        full_exams[name] = (
            await db.scalar(
                select(func.count(model.id))
                .join(User, User.id == model.user_id)
                .where(
                    *real_users(),
                    model.mode == "FULL_TEST",
                    model.status == ("COMPLETED" if name == "speaking" else "SUBMITTED"),
                )
            )
            or 0
        )
    activity = sum(completed.values())
    registration = {
        label: await db.scalar(select(func.count(User.id)).where(*real_users(), User.created_at >= since))
        or 0
        for label, since in (("today", today), ("7d", seven), ("30d", thirty))
    }
    return {
        "revenue_by_plan": [
            {"plan_code": code, "purchases": count, "revenue_vnd": int(amount)}
            for code, count, amount in revenue_by_plan
        ],
        "revenue_today_vnd": await revenue_since(today),
        "revenue_7d_vnd": await revenue_since(seven),
        "revenue_30d_vnd": await revenue_since(thirty),
        "revenue_month_vnd": int(revenue_month),
        "total_revenue_vnd": int(
            await db.scalar(
                select(func.coalesce(func.sum(Payment.amount_vnd), 0))
                .join(User)
                .where(*real_users(), Payment.status == "PAID")
            )
            or 0
        ),
        "average_revenue_per_payer_vnd": int(
            (
                await db.scalar(
                    select(func.coalesce(func.sum(Payment.amount_vnd), 0))
                    .join(User)
                    .where(*real_users(), Payment.status == "PAID")
                )
                or 0
            )
            / paid_users
        )
        if paid_users
        else None,
        "paid_transactions": purchases,
        "trial_by_feature": dict(trial_by_feature),
        "completed_practices": completed,
        "full_exams": full_exams,
        "most_practiced_skill": max(completed, key=completed.get) if activity else None,
        "average_practices_per_user": round(activity / total, 2) if total else None,
        "paid_users": paid_users,
        "converted_trial_users": converted,
        "renewal_count": max(0, purchases - paid_users),
        "expired_vip_users": expired,
        "total_users": total,
        "registrations": registration,
        "funnel": {
            "registered": total,
            "started_trial": trial_started,
            "completed_trial": trial_completed,
            "viewed_pricing": pricing_viewed,
            "started_checkout": checkout_started,
            "paid": paid_users,
            "trial_to_paid_percent": round(converted / trial_started * 100, 1) if trial_started else None,
        },
        "server_now": utcnow(),
    }


@router.get("/settings")
async def admin_settings(admin: CurrentAdmin):
    return {
        "user_custom_questions_enabled": settings.user_custom_questions_enabled,
        "free_reading_enabled": settings.free_reading_enabled,
        "free_reading_daily_limit": settings.free_reading_daily_limit,
        "free_ai_question_generation_enabled": settings.free_ai_question_generation_enabled,
        "vip_ai_question_generation_enabled": settings.vip_ai_question_generation_enabled,
        "free_trial_writing_task1_attempts": settings.free_trial_writing_task1_attempts,
        "free_trial_speaking_part1_attempts": settings.free_trial_speaking_part1_attempts,
        "vip_fair_use_enabled": settings.vip_fair_use_enabled,
        "vip_writing_daily_limit": settings.vip_writing_daily_limit,
        "vip_speaking_daily_limit": settings.vip_speaking_daily_limit,
        "vip_reading_daily_limit": settings.vip_reading_daily_limit,
        "vip_ai_generation_daily_limit": settings.vip_ai_generation_daily_limit,
        "payment_provider": "MANUAL",
    }


@router.get("/audit-logs")
async def audit_logs(db: DB, admin: CurrentAdmin, limit: int = Query(50, ge=1, le=100)):
    rows = await db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit))
    return {
        "items": [
            {
                "id": row.id,
                "admin_user_id": row.admin_user_id,
                "action": row.action,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "details": row.details,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }
