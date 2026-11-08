import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin, seed_viewer

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_kill_switch_and_rbac() -> None:
    await seed_admin()
    await seed_viewer()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        status = await client.get("/api/v1/collector/status", headers=admin)
        assert status.status_code == 200
        assert "tiers" in status.json()["data"]

        enabled = await client.post(
            "/api/v1/collector/kill-switch", json={"active": True}, headers=admin
        )
        assert enabled.status_code == 200
        assert enabled.json()["data"]["enabled"] is False

        blocked = await client.post("/api/v1/collector/run-scan", headers=admin)
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "COLLECTOR_DISABLED"

        status = await client.get("/api/v1/collector/status", headers=admin)
        assert status.json()["data"]["enabled"] is False

        restored = await client.post(
            "/api/v1/collector/kill-switch", json={"active": False}, headers=admin
        )
        assert restored.status_code == 200

        forbidden = await client.post("/api/v1/collector/run-scan", headers=viewer)
        assert forbidden.status_code == 403

        viewer_status = await client.get("/api/v1/collector/status", headers=viewer)
        assert viewer_status.status_code == 200

        missing_job = await client.get(
            "/api/v1/collector/jobs/00000000-0000-0000-0000-000000000000",
            headers=admin,
        )
        assert missing_job.status_code == 404
