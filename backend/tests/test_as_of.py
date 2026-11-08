import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.trader_metric import TraderMetric
from app.seed import seed_admin
from app.services.agent.db_tools import get_trader_profile
from app.services.screener import ScreenerFilters, list_traders

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def test_as_of_is_source_time_not_computed() -> None:
    await seed_admin()
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric)
                .where(TraderMetric.metrics.is_not(None))
                .limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        performance_at = (metric.metrics or {}).get("provenance", {}).get(
            "performance_at"
        )
        computed_at = metric.computed_at.isoformat() if metric.computed_at else None
        assert performance_at

        profile = await get_trader_profile(db, {"trader_id": trader_id})
        assert profile.error is None
        assert profile.data["as_of"] == performance_at
        assert profile.data["computed_at"] == computed_at
        assert profile.meta["as_of"] == performance_at

        listed = await list_traders(db, ScreenerFilters(), page_size=5)
        item = listed["items"][0]
        row = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.lead_portfolio_id == item["id"])
            )
        ).scalars().first()
        expected_as_of = (row.metrics or {}).get("provenance", {}).get("performance_at")
        assert item["as_of"] == expected_as_of
        assert item["computed_at"] == (
            row.computed_at.isoformat() if row.computed_at else None
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        detail = await client.get(f"/api/v1/traders/{trader_id}", headers=headers)
        assert detail.status_code == 200
        payload = detail.json()["data"]
        assert payload["as_of"] == performance_at
        assert payload["computed_at"] == computed_at
