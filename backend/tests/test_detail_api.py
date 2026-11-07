import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import SessionLocal
from app.main import app
from app.seed import seed_admin

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + dữ liệu Phase 2/3 trong compose",
)


async def _login(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def _pick_trader() -> str:
    async with SessionLocal() as db:
        from sqlalchemy import select

        from app.models.trader_metric import TraderMetric

        pid = await db.scalar(select(TraderMetric.lead_portfolio_id).limit(1))
        assert pid
        return pid


@pytest.mark.asyncio
async def test_detail_endpoints_contract() -> None:
    await seed_admin()
    pid = await _pick_trader()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)

        performance = await client.get(f"/api/v1/traders/{pid}/performance", headers=headers)
        assert performance.status_code == 200
        data = performance.json()["data"]
        assert set(data["windows"]) == {"7D", "30D", "90D", "180D"}
        assert data["benchmark"] is None
        assert isinstance(data["chart"], list)

        positions = await client.get(
            f"/api/v1/traders/{pid}/positions",
            params={"page_size": 5},
            headers=headers,
        )
        assert positions.status_code == 200
        body = positions.json()["data"]
        assert body["page_size"] == 5
        assert len(body["items"]) <= 5
        if body["items"]:
            row = body["items"][0]
            assert {"symbol", "side", "closing_pnl", "roi"} <= set(row)

        trades = await client.get(
            f"/api/v1/traders/{pid}/trades", params={"page_size": 5}, headers=headers
        )
        assert trades.status_code == 200
        assert len(trades.json()["data"]["items"]) <= 5

        transfers = await client.get(f"/api/v1/traders/{pid}/transfers", headers=headers)
        assert transfers.status_code == 200
        assert isinstance(transfers.json()["data"]["items"], list)

        risk = await client.get(f"/api/v1/traders/{pid}/risk", headers=headers)
        assert risk.status_code == 200
        assert isinstance(risk.json()["data"]["events"], list)

        score = await client.get(f"/api/v1/traders/{pid}/score", headers=headers)
        assert score.status_code == 200
        score_data = score.json()["data"]
        assert score_data["config_version"] >= 1
        assert "breakdown" in score_data


@pytest.mark.asyncio
async def test_detail_unknown_trader_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        for suffix in ("performance", "positions", "trades", "transfers", "risk", "score"):
            response = await client.get(
                f"/api/v1/traders/khong-ton-tai/{suffix}", headers=headers
            )
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "TRADER_NOT_FOUND"


@pytest.mark.asyncio
async def test_positions_filter_pagination() -> None:
    pid = await _pick_trader()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _login(client)
        page1 = await client.get(
            f"/api/v1/traders/{pid}/positions",
            params={"page_size": 2, "page": 1},
            headers=headers,
        )
        page2 = await client.get(
            f"/api/v1/traders/{pid}/positions",
            params={"page_size": 2, "page": 2},
            headers=headers,
        )
        body1 = page1.json()["data"]
        body2 = page2.json()["data"]
        assert body1["total"] == body2["total"]
        if body1["items"] and body2["items"]:
            assert body1["items"][0]["id"] != body2["items"][0]["id"]

        side_filter = await client.get(
            f"/api/v1/traders/{pid}/positions",
            params={"side": "Long", "page_size": 5},
            headers=headers,
        )
        for row in side_filter.json()["data"]["items"]:
            assert row["side"].lower().startswith("long")
