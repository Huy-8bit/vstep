"""Admin bootstrap uses disposable accounts and never resets a returning user's password."""

from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import password_hasher
from app.db.session import SessionLocal
from app.main import app
from app.models import User
from app.services.initial_admin import InitialAdminBootstrapService, validate_initial_password


@pytest.mark.asyncio
async def test_initial_admin_create_and_idempotent_login():
    email = f"bootstrap-{uuid4().hex}@example.com"
    original_password = "BootstrapPass2026!"
    replacement_password = "UserChangedPass2026!"
    config = settings.model_copy(
        update={
            "initial_admin_enabled": True,
            "initial_admin_email": email,
            "initial_admin_password": original_password,
            "initial_admin_name": "First Admin",
        }
    )
    try:
        await InitialAdminBootstrapService(config).run()
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            assert user and user.role == "ADMIN" and user.status == "ACTIVE"
            assert user.name == "First Admin" and user.is_test_account is False
            assert user.password_hash != original_password
            assert password_hasher.verify(original_password, user.password_hash)
            user.password_hash = password_hasher.hash(replacement_password)
            original_id = user.id
            await db.commit()
        await InitialAdminBootstrapService(config).run()
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            assert user and user.id == original_id
            assert password_hasher.verify(replacement_password, user.password_hash)
            assert not password_hasher.verify(original_password, user.password_hash)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Origin": settings.frontend_url, "Sec-Fetch-Site": "cross-site"},
        ) as client:
            response = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": replacement_password}
            )
            assert response.status_code == 200, response.text
            assert response.json()["role"] == "ADMIN"
            admin = await client.get("/api/v1/admin/dashboard")
            assert admin.status_code == 200, admin.text
            denied = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": replacement_password},
                headers={"Origin": "https://untrusted.example"},
            )
            assert denied.status_code == 403
    finally:
        async with SessionLocal() as db:
            await db.execute(delete(User).where(User.email == email))
            await db.commit()


def test_initial_admin_rejects_placeholder_passwords():
    for value in ("change-me", "Password123456", "abcdefghijk", "aaaaaaaaaa12"):
        with pytest.raises(ValueError):
            validate_initial_password(value, "admin@example.com")


@pytest.mark.asyncio
async def test_existing_user_is_promoted_without_password_change():
    email = f"promote-{uuid4().hex}@example.com"
    original_password = "OriginalUserPass2026!"
    try:
        async with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=password_hasher.hash(original_password),
                role="USER",
                status="ACTIVE",
            )
            db.add(user)
            await db.commit()
        config = settings.model_copy(
            update={
                "initial_admin_enabled": True,
                "initial_admin_email": email,
                "initial_admin_password": "",
            }
        )
        await InitialAdminBootstrapService(config).run()
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            assert user and user.role == "ADMIN"
            assert password_hasher.verify(original_password, user.password_hash)
    finally:
        async with SessionLocal() as db:
            await db.execute(delete(User).where(User.email == email))
            await db.commit()
