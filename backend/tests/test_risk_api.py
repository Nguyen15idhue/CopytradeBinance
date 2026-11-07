import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed import seed_admin

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + risk_events trong compose",
)


@pytest.mark.asyncio
async def test_risk_monitor_api() -> None:
    await seed_admin()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
        )
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

        summary = await client.get("/api/v1/risk/summary", headers=headers)
        assert summary.status_code == 200
        assert summary.json()["data"]["total"] > 0

        events = await client.get(
            "/api/v1/risk/events", params={"severity": "critical", "page_size": 5}, headers=headers
        )
        assert events.status_code == 200
        body = events.json()["data"]
        assert body["items"]
        first = body["items"][0]
        assert first["severity"] == "critical"
        assert first["evidence"]
        assert {"field", "value", "threshold"} <= set(first["evidence"])
        assert first["trader_id"]

        filtered = await client.get(
            "/api/v1/risk/events",
            params={"trader": first["trader_id"], "page_size": 50},
            headers=headers,
        )
        assert all(
            item["trader_id"] == first["trader_id"] for item in filtered.json()["data"]["items"]
        )
