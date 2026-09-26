import logging
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.api.deps import DB, CurrentUser
from app.common.errors import AppError
from app.core.config import settings
from app.core.identity import normalize_email
from app.core.security import (
    DUMMY_HASH,
    decode_token,
    make_token,
    password_hasher,
    token_hash,
)
from app.db.base import utcnow
from app.models import AuthSession, User
from app.schemas.api import Credentials
from app.services.ai_cost_service import is_cost_admin
from app.services.entitlements import EntitlementService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def set_tokens(response: Response, user: User, session: AuthSession) -> None:
    refresh = make_token(user.id, session.id, "refresh")
    session.refresh_hash = token_hash(refresh)
    options = {
        "httponly": True,
        "secure": settings.app_env == "production" or settings.cookie_samesite == "none",
        "samesite": settings.cookie_samesite,
        "path": "/api",
    }
    response.set_cookie(
        "vstep_access",
        make_token(user.id, session.id, "access"),
        max_age=settings.jwt_access_expire_minutes * 60,
        **options,
    )
    response.set_cookie(
        "vstep_refresh",
        refresh,
        max_age=settings.jwt_refresh_expire_days * 86400,
        **options,
    )
    response.headers["Cache-Control"] = "no-store"


async def start_session(response: Response, db, user: User):
    session = AuthSession(
        id=str(uuid4()),
        user_id=user.id,
        expires_at=utcnow() + timedelta(days=settings.jwt_refresh_expire_days),
    )
    set_tokens(response, user, session)
    db.add(session)
    user.last_login_at = utcnow()
    await db.commit()
    return await user_view(db, user)


async def user_view(db, user: User):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "joined_at": user.created_at,
        "learning_goal": user.learning_goal,
        "is_ai_admin": user.role == "ADMIN" or is_cost_admin(user),
        "access": await EntitlementService(db).summary(user),
    }


@router.post("/register", status_code=201)
async def register(data: Credentials, response: Response, db: DB):
    email = normalize_email(str(data.email))
    existing = await db.scalar(select(User.id).where(func.lower(func.trim(User.email)) == email))
    if existing:
        raise AppError(409, "Email này đã được đăng ký.")
    user = User(
        email=email,
        password_hash=await run_in_threadpool(password_hasher.hash, data.password),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise AppError(409, "Email này đã được đăng ký.") from None
    from app.models.commerce import ProductEvent

    db.add(ProductEvent(user_id=user.id, name="USER_REGISTERED", details={}))
    return await start_session(response, db, user)


@router.post("/login")
async def login(data: Credentials, response: Response, db: DB):
    user = await db.scalar(
        select(User).where(func.lower(func.trim(User.email)) == normalize_email(str(data.email)))
    )
    valid = await run_in_threadpool(
        password_hasher.verify,
        data.password,
        user.password_hash if user else DUMMY_HASH,
    )
    if not valid or not user:
        logger.info("auth_login_failed reason=INVALID_CREDENTIALS")
        raise AppError(401, "Email hoặc mật khẩu không đúng.")
    if user.status != "ACTIVE":
        logger.info("auth_login_failed reason=ACCOUNT_DISABLED user_id=%s", user.id)
        raise AppError(403, "Tài khoản đã bị vô hiệu hóa.", "ACCOUNT_DISABLED")
    result = await start_session(response, db, user)
    logger.info("auth_login_succeeded user_id=%s role=%s", user.id, user.role)
    return result


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: DB):
    raw = request.cookies.get("vstep_refresh")
    payload = decode_token(raw, "refresh")
    session = await db.scalar(select(AuthSession).where(AuthSession.id == payload["sid"]).with_for_update())
    if (
        not session
        or session.user_id != payload["sub"]
        or session.revoked_at
        or session.expires_at <= utcnow()
        or session.refresh_hash != token_hash(raw or "")
    ):
        raise AppError(401, "Phiên đăng nhập đã hết hạn.", "unauthorized")
    user = await db.get(User, session.user_id)
    if not user or user.status != "ACTIVE":
        raise AppError(403, "Tài khoản đã bị vô hiệu hóa.", "ACCOUNT_DISABLED")
    session.expires_at = utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    set_tokens(response, user, session)
    await db.commit()
    return await user_view(db, user)


@router.post("/logout")
async def logout(request: Request, response: Response, db: DB):
    try:
        payload = decode_token(request.cookies.get("vstep_refresh"), "refresh")
        session = await db.get(AuthSession, payload["sid"])
        if session and session.user_id == payload["sub"]:
            session.revoked_at = utcnow()
            await db.commit()
    except AppError:
        pass
    response.delete_cookie(
        "vstep_access",
        path="/api",
        samesite=settings.cookie_samesite,
        secure=settings.app_env == "production" or settings.cookie_samesite == "none",
    )
    response.delete_cookie(
        "vstep_refresh",
        path="/api",
        samesite=settings.cookie_samesite,
        secure=settings.app_env == "production" or settings.cookie_samesite == "none",
    )
    return {"message": "Đã đăng xuất."}


@router.get("/me")
async def me(user: CurrentUser, db: DB):
    return await user_view(db, user)
