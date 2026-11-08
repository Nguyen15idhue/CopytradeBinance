import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models.trader_metric import TraderMetric
from app.seed import seed_admin
from app.services.screener import ScreenerFilters, list_traders, risk_score_missing

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


def test_risk_score_missing_helper() -> None:
    assert risk_score_missing(0) is True
    assert risk_score_missing(1) is False


async def test_risk_score_backfilled() -> None:
    await seed_admin()
    async with SessionLocal() as db:
        scored = await db.scalar(
            select(func.count())
            .select_from(TraderMetric)
            .where(TraderMetric.risk_score.is_not(None))
        )
        total = await db.scalar(select(func.count()).select_from(TraderMetric))
        assert int(scored or 0) > 0
        missing = await db.scalar(
            select(func.count())
            .select_from(TraderMetric)
            .where(TraderMetric.risk_score.is_(None))
        )
        # Chỉ trader chưa có dòng trader_metrics mới thiếu; không quá 5% tổng.
        assert int(missing or 0) <= max(5, int(total or 0) * 0.05)


async def test_filter_max_risk_score_and_meta() -> None:
    await seed_admin()
    async with SessionLocal() as db:
        result = await list_traders(
            db, ScreenerFilters(max_risk_score=40), page_size=20
        )
        assert result["items"]
        for item in result["items"]:
            assert item["risk_score"] is not None
            assert item["risk_score"] <= 40
        assert result["risk_score_missing"] is False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        response = await client.get(
            "/api/v1/traders", params={"max_risk_score": 40, "page_size": 10},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["risk_score_missing"] is False
        assert all(item["risk_score"] <= 40 for item in data["items"])
