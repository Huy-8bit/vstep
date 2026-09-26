"""Read-only administrator diagnosis; never prints secrets or password hashes."""

import argparse
import asyncio

from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.identity import normalize_email
from app.core.security import password_hasher
from app.db.session import SessionLocal, engine
from app.models import User


async def check_admin(email: str, verify_env_password: bool = False) -> dict[str, object]:
    result: dict[str, object] = {
        "bootstrap_enabled": settings.initial_admin_enabled,
        "configured_email": bool(settings.initial_admin_email.strip()),
        "configured_password": bool(settings.initial_admin_password),
        "account_exists": False,
    }
    async with SessionLocal() as db:
        user = await db.scalar(
            select(User).where(func.lower(func.trim(User.email)) == normalize_email(email))
        )
        if user:
            result.update(
                account_exists=True,
                role=user.role,
                status=user.status,
                password_hash_present=bool(user.password_hash),
            )
            if verify_env_password:
                result["configured_password_matches"] = (
                    await run_in_threadpool(
                        password_hasher.verify, settings.initial_admin_password, user.password_hash
                    )
                    if settings.initial_admin_password and user.password_hash
                    else False
                )
    return result


async def main(email: str, verify_env_password: bool) -> None:
    try:
        result = await check_admin(email, verify_env_password)
        for key, value in result.items():
            print(f"{key}: {value}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Admin bootstrap and account status without showing secrets."
    )
    parser.add_argument("--email", default=settings.initial_admin_email, help="Account to inspect")
    parser.add_argument(
        "--verify-env-password", action="store_true", help="Show only whether the configured password matches"
    )
    args = parser.parse_args()
    if not normalize_email(args.email):
        parser.error("Set INITIAL_ADMIN_EMAIL or pass --email.")
    asyncio.run(main(args.email, args.verify_env_password))
