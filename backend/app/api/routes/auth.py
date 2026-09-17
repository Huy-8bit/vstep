from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.api.deps import DB, CurrentUser
from app.common.errors import AppError
from app.core.config import settings
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

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_tokens(response: Response, user: User, session: AuthSession) -> None:
    refresh = make_token(user.id, session.id, "refresh")
    session.refresh_hash = token_hash(refresh)
    options = {
        "httponly": True,
        "secure": settings.app_env == "production",
        "samesite": "lax",
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
    await db.commit()
    return {"id": user.id, "email": user.email}


@router.post("/register", status_code=201)
async def register(data: Credentials, response: Response, db: DB):
    user = User(
        email=str(data.email).strip().lower(),
        password_hash=await run_in_threadpool(password_hasher.hash, data.password),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise AppError(409, "Email này đã được đăng ký.") from None
    return await start_session(response, db, user)


@router.post("/login")
async def login(data: Credentials, response: Response, db: DB):
    user = await db.scalar(select(User).where(User.email == str(data.email).strip().lower()))
    valid = await run_in_threadpool(
        password_hasher.verify,
        data.password,
        user.password_hash if user else DUMMY_HASH,
    )
    if not valid or not user:
        raise AppError(401, "Email hoặc mật khẩu không đúng.")
    return await start_session(response, db, user)


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
    session.expires_at = utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    set_tokens(response, user, session)
    await db.commit()
    return {"id": user.id, "email": user.email}


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
    response.delete_cookie("vstep_access", path="/api")
    response.delete_cookie("vstep_refresh", path="/api")
    return {"message": "Đã đăng xuất."}


@router.get("/me")
async def me(user: CurrentUser):
    return {"id": user.id, "email": user.email}
