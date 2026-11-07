import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin, seed_viewer

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + ranking snapshots trong compose",
)


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_ranking_boards_contract_and_run() -> None:
    await seed_admin()
    await seed_viewer()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        for board in ("overall", "low_risk", "consistency"):
            response = await client.get(
                "/api/v1/ranking", params={"board": board}, headers=viewer
            )
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["board"] == board
            assert data["total"] == len(data["items"])
            if data["items"]:
                assert data["config_version"] >= 1
                item = data["items"][0]
                assert {"rank", "id", "score", "tier", "risk_level"} <= set(item)

        invalid = await client.get(
            "/api/v1/ranking", params={"board": "unknown"}, headers=viewer
        )
        assert invalid.status_code == 422

        forbidden = await client.post("/api/v1/ranking/run", headers=viewer)
        assert forbidden.status_code == 403

        run = await client.post("/api/v1/ranking/run", headers=admin)
        assert run.status_code == 200
        assert run.json()["data"]["boards"]["overall"] > 0
