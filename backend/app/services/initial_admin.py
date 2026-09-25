"""Idempotent, environment-controlled first-admin bootstrap."""

import logging
import re

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.security import password_hasher
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models import AuthSession, User
from app.models.commerce import AdminAuditLog

logger = logging.getLogger(__name__)


def validate_initial_password(password: str, email: str) -> None:
    lowered = password.lower().strip()
    forbidden = ("change-me", "changeme", "password", "admin123", "123456", "example", "default")
    if (
        len(password) < 12
        or any(word in lowered for word in forbidden)
        or lowered == email.split("@", 1)[0]
        or len(set(password)) < 6
        or not re.search(r"[a-zA-Z]", password)
        or not re.search(r"\d", password)
    ):
        raise ValueError(
            "INITIAL_ADMIN_PASSWORD must have at least 12 varied characters, letters and digits; "
            "known placeholders are not allowed."
        )


class InitialAdminBootstrapService:
    def __init__(self, config: Settings):
        self.config = config

    async def run(self) -> None:
        if not self.config.initial_admin_enabled:
            return
        if not self.config.initial_admin_email.strip():
            logger.warning(
                "Initial admin bootstrap enabled but INITIAL_ADMIN_EMAIL is missing; no account created."
            )
            return
        email = str(TypeAdapter(EmailStr).validate_python(self.config.initial_admin_email.strip())).lower()
        password = self.config.initial_admin_password
        if password:
            validate_initial_password(password, email)
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email).with_for_update())
            if user is None:
                if not password:
                    logger.error(
                        "Initial admin bootstrap needs INITIAL_ADMIN_PASSWORD to create a new account; no account created."
                    )
                    return
                user = User(
                    email=email,
                    name=self.config.initial_admin_name.strip() or "Admin",
                    password_hash=await run_in_threadpool(password_hasher.hash, password),
                    role="ADMIN",
                    status="ACTIVE",
                    is_test_account=False,
                )
                db.add(user)
                try:
                    await db.flush()
                except IntegrityError:
                    await db.rollback()
                    user = await db.scalar(select(User).where(User.email == email).with_for_update())
                    if user is None:
                        raise
                else:
                    db.add(
                        AdminAuditLog(
                            admin_user_id=user.id,
                            action="BOOTSTRAP_ADMIN",
                            target_type="USER",
                            target_id=user.id,
                            details={"created": True},
                        )
                    )
                    await db.commit()
                    logger.info("Initial admin account created for configured email.")
                    return
            if user.role != "ADMIN":
                user.role = "ADMIN"
                await db.execute(
                    update(AuthSession)
                    .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
                    .values(revoked_at=utcnow())
                )
                db.add(
                    AdminAuditLog(
                        admin_user_id=user.id,
                        action="BOOTSTRAP_ADMIN",
                        target_type="USER",
                        target_id=user.id,
                        details={"created": False},
                    )
                )
                await db.commit()
                logger.info("Existing account promoted to initial admin; its password was preserved.")
