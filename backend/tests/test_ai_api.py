import os
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.main import app
from app.models.ai_report import AIReport, AIUsage
from app.models.trader_metric import TraderMetric
from app.seed import seed_admin, seed_viewer
from app.services.ai.openrouter import AIResult
from app.services.ai.prompt import template_report

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + metrics trong compose",
)


async def _ids(limit: int = 2) -> list[str]:
    async with SessionLocal() as db:
        rows = await db.execute(select(TraderMetric.lead_portfolio_id).limit(limit))
        return [row[0] for row in rows.all()]


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with SessionLocal() as db:
        await db.execute(delete(AIReport))
        await db.execute(delete(AIUsage))
        await db.commit()


@pytest.mark.asyncio
async def test_analyze_admin_cached_and_score_unchanged(monkeypatch) -> None:
    await seed_admin()
    await seed_viewer()
    trader_id = (await _ids(1))[0]

    async def fake_generate(context, api_key, transport=None, **kwargs):
        result = AIResult(
            payload=template_report(context),
            role="primary",
            model="fake-model",
            prompt_tokens=10,
            completion_tokens=20,
            cost_usd=0,
            latency_ms=120,
        )
        return result, []

    monkeypatch.setattr("app.services.ai.service.generate_report", fake_generate)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        before = await client.get(f"/api/v1/traders/{trader_id}/score", headers=admin)
        score_before = before.json()["data"]["score"]

        first = await client.post(f"/api/v1/ai/analyze/{trader_id}", headers=admin)
        assert first.status_code == 200, first.text
        data = first.json()["data"]
        assert data["cached"] is False
        assert data["report"]["model_role"] == "primary"
        assert data["report"]["evidence_ids"]
        assert data["report"]["cost_usd"] == 0

        second = await client.post(f"/api/v1/ai/analyze/{trader_id}", headers=admin)
        assert second.status_code == 200
        assert second.json()["data"]["cached"] is True
        assert second.json()["data"]["report"]["id"] == data["report"]["id"]

        listed = await client.get(f"/api/v1/ai/reports/{trader_id}", headers=admin)
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1

        report_id = data["report"]["id"]
        detail = await client.get(
            f"/api/v1/ai/reports/{trader_id}/{report_id}", headers=admin
        )
        assert detail.status_code == 200
        missing = await client.get(f"/api/v1/ai/reports/{trader_id}/999999", headers=admin)
        assert missing.status_code == 404

        forbidden = await client.post(f"/api/v1/ai/analyze/{trader_id}", headers=viewer)
        assert forbidden.status_code == 403

        after = await client.get(f"/api/v1/traders/{trader_id}/score", headers=admin)
        assert after.json()["data"]["score"] == score_before


@pytest.mark.asyncio
async def test_budget_exceeded_blocks_call(monkeypatch) -> None:
    await seed_admin()
    ids = await _ids(2)
    trader_id = ids[1]

    async with SessionLocal() as db:
        await db.execute(delete(AIReport).where(AIReport.lead_portfolio_id == trader_id))
        db.add(
            AIUsage(
                day=date.today(),
                model="fake-model",
                prompt_tokens=1,
                completion_tokens=1,
                cost_usd=999,
            )
        )
        await db.commit()

    async def fake_generate(context, api_key, transport=None):
        raise AssertionError("không được gọi model khi vượt budget")

    monkeypatch.setattr("app.services.ai.service.generate_report", fake_generate)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        response = await client.post(f"/api/v1/ai/analyze/{trader_id}", headers=admin)
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "AI_BUDGET_EXCEEDED"
