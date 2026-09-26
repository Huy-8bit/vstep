import logging
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.core.security import decode_token
from app.db.base import utcnow
from app.db.session import get_db
from app.models import AuthSession, User

logger = logging.getLogger(__name__)

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
    if user.status != "ACTIVE":
        raise AppError(403, "Tài khoản đã bị vô hiệu hóa.", "ACCOUNT_DISABLED")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def current_admin(user: CurrentUser) -> User:
    if user.role != "ADMIN":
        logger.info("admin_authorization_rejected user_id=%s role=%s", user.id, user.role)
        raise AppError(403, "Chỉ quản trị viên được truy cập.", "ADMIN_REQUIRED")
    return user


CurrentAdmin = Annotated[User, Depends(current_admin)]
