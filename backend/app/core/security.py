import hashlib
from datetime import timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.common.errors import AppError
from app.core.config import settings
from app.db.base import utcnow

password_hasher = PasswordHash.recommended()
# Use the same expensive verification path for unknown accounts.
DUMMY_HASH = password_hasher.hash("not-an-account-password")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def make_token(user_id: str, session_id: str, kind: str) -> str:
    now = utcnow()
    duration = (
        timedelta(minutes=settings.jwt_access_expire_minutes)
        if kind == "access"
        else timedelta(days=settings.jwt_refresh_expire_days)
    )
    return jwt.encode(
        {
            "sub": user_id,
            "sid": session_id,
            "type": kind,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + duration,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_token(token: str | None, kind: str) -> dict:
    try:
        data = jwt.decode(
            token or "",
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "sid", "type", "jti"]},
        )
        if data["type"] != kind:
            raise jwt.InvalidTokenError()
        return data
    except jwt.InvalidTokenError:
        raise AppError(401, "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", "unauthorized") from None
