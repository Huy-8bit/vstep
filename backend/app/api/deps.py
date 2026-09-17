from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.core.security import decode_token
from app.db.base import utcnow
from app.db.session import get_db
from app.models import AuthSession, User

DB = Annotated[AsyncSession, Depends(get_db)]


async def current_user(request: Request, db: DB) -> User:
    payload = decode_token(request.cookies.get("vstep_access"), "access")
    session = await db.get(AuthSession, payload["sid"])
    if (
        not session
        or session.user_id != payload["sub"]
        or session.revoked_at
        or session.expires_at <= utcnow()
    ):
        raise AppError(401, "Phiên đăng nhập đã hết hạn.", "unauthorized")
    user = await db.get(User, payload["sub"])
    if not user:
        raise AppError(401, "Tài khoản không tồn tại.", "unauthorized")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
