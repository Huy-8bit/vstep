import httpx
import pytest

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_browser_preflight_allows_registration_headers():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": settings.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "cache-control,content-type,pragma",
            },
        )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == settings.frontend_url
    allowed = response.headers["Access-Control-Allow-Headers"].lower()
    assert all(header in allowed for header in ("cache-control", "content-type", "pragma"))


@pytest.mark.asyncio
async def test_browser_preflight_rejects_unknown_origin():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 400
    assert "Access-Control-Allow-Origin" not in response.headers
