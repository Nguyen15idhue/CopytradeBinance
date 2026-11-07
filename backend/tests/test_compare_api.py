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


async def _ids(limit: int = 2) -> list[str]:
    async with SessionLocal() as db:
        from sqlalchemy import select

        from app.models.trader_metric import TraderMetric

        rows = await db.execute(select(TraderMetric.lead_portfolio_id).limit(limit))
        return [row[0] for row in rows.all()]


async def _headers(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_compare_two_traders_contract() -> None:
    await seed_admin()
    ids = await _ids(2)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _headers(client)
        response = await client.get(f"/api/v1/compare?ids={','.join(ids)}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 2
        assert data["correlation"]["ids"] == ids
        assert len(data["correlation"]["matrix"]) == 2
        assert "ước tính" in data["correlation"]["disclaimer"]
        assert data["correlation"]["matrix"][0][0] == 1.0
        assert set(data["series"]) == set(ids)


@pytest.mark.asyncio
async def test_compare_rejects_wrong_count() -> None:
    ids = await _ids(2)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _headers(client)
        single = await client.get(f"/api/v1/compare?ids={ids[0]}", headers=headers)
        assert single.status_code == 422
        assert single.json()["error"]["code"] == "INVALID_COMPARE"
