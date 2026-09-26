"""Explicit administrator password recovery; never prints or logs the password."""

import argparse
import asyncio
import getpass
import stat
from pathlib import Path

from sqlalchemy import func, select, update
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.identity import normalize_email
from app.core.security import password_hasher
from app.db.base import utcnow
from app.db.session import SessionLocal, engine
from app.models import AuthSession, User
from app.models.commerce import AdminAuditLog
from app.services.initial_admin import validate_initial_password


def read_password_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Password file must be a regular file, not a symlink.")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("Password file must be readable only by its owner (chmod 600).")
    return path.read_text().rstrip("\r\n")


async def reset_admin_password(email: str, password: str) -> None:
    normalized = normalize_email(email)
    validate_initial_password(password, normalized)
    async with SessionLocal() as db:
        user = await db.scalar(
            select(User).where(func.lower(func.trim(User.email)) == normalized).with_for_update()
        )
        if not user:
            raise ValueError("Admin account does not exist; create it first.")
        if user.role != "ADMIN":
            raise ValueError("Account is not ADMIN; password was not changed.")
        user.password_hash = await run_in_threadpool(password_hasher.hash, password)
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        db.add(
            AdminAuditLog(
                admin_user_id=user.id,
                action="ADMIN_PASSWORD_RESET_CLI",
                target_type="USER",
                target_id=user.id,
                details={"method": "explicit_cli"},
            )
        )
        await db.commit()


async def main(email: str, password: str) -> None:
    try:
        await reset_admin_password(email, password)
        print("Admin password reset; previous sessions were revoked. Account status was unchanged.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explicitly reset an existing Admin password.")
    parser.add_argument("--email", default=settings.initial_admin_email, help="Existing Admin email")
    parser.add_argument("--password-file", type=Path, help="Owner-only file for noninteractive recovery")
    args = parser.parse_args()
    email = normalize_email(args.email)
    if not email or "@" not in email:
        parser.error("Set INITIAL_ADMIN_EMAIL or pass a valid --email.")
    try:
        if args.password_file:
            password = read_password_file(args.password_file)
        else:
            password = getpass.getpass("New admin password: ")
            if password != getpass.getpass("Confirm new admin password: "):
                parser.error("Passwords did not match; nothing changed.")
        validate_initial_password(password, email)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    try:
        asyncio.run(main(email, password))
    except ValueError as exc:
        parser.error(str(exc))
