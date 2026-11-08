import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.trader_metric import TraderMetric
from app.seed import seed_admin
from app.services.agent.db_tools import get_trader_profile
from app.services.freshness import STALE_MINUTES, VERY_STALE_MINUTES, level, payload

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def test_level_boundaries() -> None:
    assert level(None) == "unknown"
    assert level(149) == "ok"
    assert level(150) == "ok"
    assert level(151) == "stale"
    assert level(1440) == "stale"
    assert level(1441) == "very_stale"
    assert payload(151)["stale_minutes"] == STALE_MINUTES
    assert payload(2000)["very_stale_minutes"] == VERY_STALE_MINUTES


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def test_api_exposes_freshness() -> None:
    await seed_admin()
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.metrics.is_not(None)).limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        expected = (metric.metrics or {}).get("freshness_minutes")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)

        detail = await client.get(f"/api/v1/traders/{trader_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        freshness = detail.json()["data"]["freshness"]
        assert set(freshness) >= {"minutes", "level", "as_of"}
        assert freshness["minutes"] == pytest.approx(expected, abs=0.01) if expected else True
        assert freshness["level"] in {"ok", "stale", "very_stale", "unknown"}

        perf = await client.get(
            f"/api/v1/traders/{trader_id}/performance", headers=headers
        )
        assert perf.status_code == 200
        assert "freshness" in perf.json()["data"]

        listed = await client.get(
            "/api/v1/traders", params={"page_size": 5}, headers=headers
        )
        assert listed.status_code == 200
        items = listed.json()["data"]["items"]
        assert items and "freshness" in items[0]


async def test_agent_profile_has_freshness_evidence() -> None:
    await seed_admin()
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.metrics.is_not(None)).limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        result = await get_trader_profile(db, {"trader_id": trader_id})
        assert result.error is None
        assert "freshness" in result.data
        labels = {item.id for item in result.evidence}
        assert f"{trader_id}:freshness_minutes" in labels or result.data["freshness"][
            "minutes"
        ] is None
