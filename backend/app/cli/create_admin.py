"""Bootstrap a known admin account after migrations: python -m app.cli.create_admin email."""

import argparse
import asyncio
import getpass

from sqlalchemy import func, select, update

from app.core.config import settings
from app.core.identity import normalize_email
from app.core.security import password_hasher
from app.db.base import utcnow
from app.db.session import SessionLocal, engine
from app.models import AuthSession, User
from app.models.commerce import AdminAuditLog
from app.services.initial_admin import validate_initial_password


async def main(email: str, password: str | None, new_account: bool = False, name: str = "Admin"):
    async with SessionLocal() as db:
        user = await db.scalar(
            select(User).where(func.lower(func.trim(User.email)) == email).with_for_update()
        )
        if user is None:
            if password is None:
                raise SystemExit(
                    "Tài khoản chưa tồn tại. Dùng --new-account và nhập mật khẩu để tạo admin ban đầu."
                )
            user = User(
                email=email,
                name=name,
                password_hash=password_hasher.hash(password),
                role="ADMIN",
                status="ACTIVE",
                is_test_account=False,
            )
            db.add(user)
            await db.flush()
        else:
            if new_account:
                raise SystemExit("Tài khoản đã tồn tại; dùng reset_admin_password để đổi mật khẩu.")
            user.role = "ADMIN"
            user.status = "ACTIVE"
            if password is not None:
                raise SystemExit("Dùng reset_admin_password để đổi mật khẩu tài khoản đã tồn tại.")
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
                details={"email": email},
            )
        )
        await db.commit()
        print(f"Admin ready: {email}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote an existing user or create the first admin.")
    parser.add_argument("email", nargs="?", default=settings.initial_admin_email)
    parser.add_argument(
        "--email", dest="email_option", help="Admin email (alternative to positional argument)"
    )
    parser.add_argument("--name", default=settings.initial_admin_name, help="Display name for a new account")
    parser.add_argument(
        "--new-account", action="store_true", help="Create a new account with a prompted password"
    )
    parser.add_argument(
        "--reset-password", action="store_true", help="Prompt for a new password on an existing account"
    )
    args = parser.parse_args()
    email = normalize_email(args.email_option or args.email)
    if not email or "@" not in email:
        parser.error("Provide a valid admin email or set INITIAL_ADMIN_EMAIL.")
    password = (
        getpass.getpass("Admin password (12+ chars): ") if args.new_account or args.reset_password else None
    )
    if password is not None:
        if password != getpass.getpass("Confirm admin password: "):
            parser.error("Passwords did not match; nothing changed.")
        try:
            validate_initial_password(password, email)
        except ValueError as exc:
            parser.error(str(exc))
    if args.reset_password:
        from app.cli.reset_admin_password import main as reset_main

        asyncio.run(reset_main(email, password))
        raise SystemExit(0)
    asyncio.run(main(email, password, args.new_account, args.name))
