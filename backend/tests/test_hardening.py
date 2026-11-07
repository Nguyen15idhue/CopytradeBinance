import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.main import API_HITS, app
from app.models.app_setting import AppSetting
from app.seed import seed_admin, seed_viewer
from app.services.crypto import decrypt_secret, encrypt_secret

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + nginx trong compose",
)


def test_crypto_roundtrip_and_wrong_key() -> None:
    secret = "sk-or-test-secret-value"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert decrypt_secret(encrypted) == secret


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_api_key_encrypted_and_not_returned() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        secret = "sk-or-unit-test-key-123"
        updated = await client.put(
            "/api/v1/settings", json={"ai": {"api_key": secret}}, headers=admin
        )
        assert updated.status_code == 200, updated.text
        snapshot = await client.get("/api/v1/settings", headers=admin)
        body = snapshot.text
        assert secret not in body
        assert snapshot.json()["data"]["ai"]["key_configured"] is True
        assert "••••" in body

    async with SessionLocal() as db:
        row = (
            await db.execute(select(AppSetting).where(AppSetting.key == "ai.openrouter_key"))
        ).scalars().first()
        assert row is not None
        stored = row.value.get("value")
        assert secret not in str(stored)
        assert decrypt_secret(stored) == secret
        await db.execute(
            AppSetting.__table__.delete().where(AppSetting.key == "ai.openrouter_key")
        )
        await db.commit()


@pytest.mark.asyncio
async def test_metrics_and_nginx_security_headers() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "collector_last_scan_success_timestamp" in response.text

    async with AsyncClient(base_url="http://nginx", timeout=10) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "default-src 'self'" in response.headers.get("content-security-policy", "")
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_api_rate_limit_per_user(monkeypatch) -> None:
    await seed_viewer()
    settings = get_settings()
    monkeypatch.setattr(settings, "api_rate_limit_per_min", 3)
    API_HITS.clear()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")
            first = await client.get("/api/v1/settings", headers=viewer)
            second = await client.get("/api/v1/settings", headers=viewer)
            third = await client.get("/api/v1/settings", headers=viewer)
            fourth = await client.get("/api/v1/settings", headers=viewer)
            assert first.status_code == 200
            assert second.status_code == 200
            assert third.status_code == 200
            assert fourth.status_code == 429
            assert fourth.json()["error"]["code"] == "RATE_LIMITED"
    finally:
        monkeypatch.setattr(settings, "api_rate_limit_per_min", 100)
        API_HITS.clear()
