import os

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.seed import seed_admin, seed_viewer
from app.services.settings_service import SettingsUpdate

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + scoring config trong compose",
)


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_settings_validation_rejects_bad_weights() -> None:
    with pytest.raises(ValidationError):
        SettingsUpdate(scoring={"weights": {"unknown_group": 10}})
    with pytest.raises(ValidationError):
        SettingsUpdate(scoring={"weights": {"risk_management": 0}})
    with pytest.raises(ValidationError):
        SettingsUpdate(scoring={"weights": {"risk_management": 150}})


@pytest.mark.asyncio
async def test_settings_version_preview_rollback() -> None:
    await seed_admin()
    await seed_viewer()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        snapshot = await client.get("/api/v1/settings", headers=viewer)
        assert snapshot.status_code == 200
        data = snapshot.json()["data"]
        assert data["scoring"]["version"] >= 1
        assert "api_key" not in str(data["ai"]).lower()
        assert data["ai"]["key_configured"] is True

        original_version = data["scoring"]["version"]
        weights = dict(data["scoring"]["weights"])
        weights["risk_management"] = 20
        weights["profitability"] = 20

        updated = await client.put(
            "/api/v1/settings",
            json={"scoring": {"weights": weights}},
            headers=admin,
        )
        assert updated.status_code == 200, updated.text
        new_version = updated.json()["data"]["scoring"]["version"]
        assert new_version > original_version
        assert updated.json()["data"]["scoring"]["weights"]["risk_management"] == 20

        preview = await client.post(
            "/api/v1/settings/preview", json={"weights": weights}, headers=admin
        )
        assert preview.status_code == 200
        assert preview.json()["data"]["traders"] > 0
        assert "top_changes" in preview.json()["data"]

        versions = await client.get("/api/v1/settings/versions", headers=admin)
        assert any(row["version"] == new_version for row in versions.json()["data"])

        rollback = await client.post(
            f"/api/v1/settings/rollback/{original_version}", headers=admin
        )
        assert rollback.status_code == 200
        assert rollback.json()["data"]["scoring"]["version"] == original_version

        forbidden = await client.put(
            "/api/v1/settings", json={"scoring": {"weights": weights}}, headers=viewer
        )
        assert forbidden.status_code == 403

    async with SessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(AuditLog))
        assert count and count >= 2
