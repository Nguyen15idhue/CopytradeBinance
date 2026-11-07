import os
from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.agent import AgentSession, AgentToolCall
from app.models.ai_report import AIUsage
from app.services.agent.model_client import AgentModelResult, AgentToolCallRequest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


@pytest.mark.asyncio
async def test_retention_cleanup() -> None:
    from app.agent_retention import cleanup_agent_sessions
    from app.models.user import User
    from app.seed import seed_admin

    await seed_admin()
    async with SessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == "admin@example.com"))
        ).scalars().first()
        assert user is not None
        old = AgentSession(
            user_id=user.id, title="cũ", model="m",
            created_at=datetime.now().astimezone() - timedelta(days=100),
            updated_at=datetime.now().astimezone() - timedelta(days=100),
        )
        db.add(old)
        await db.commit()
        old_id = old.id
        stats = await cleanup_agent_sessions(90)
        assert stats["deleted_sessions"] >= 1
        db.expire_all()
        assert await db.get(AgentSession, old_id) is None


@pytest.mark.asyncio
async def test_model_failure_template_fallback_and_cost_logged(monkeypatch) -> None:
    from app.main import app
    from app.seed import seed_admin, seed_viewer
    from app.services.agent import orchestrator as orch
    from app.services.ai.openrouter import AIError

    await seed_admin()
    await seed_viewer()

    async def fake_fail(messages, specs, api_key, transport=None, **kwargs):
        if not hasattr(fake_fail, "called"):
            fake_fail.called = True
            return AgentModelResult(
                text="", tool_calls=[AgentToolCallRequest(name="get_data_health", arguments={})],
                role="primary",
            ), []
        raise AIError("primary/mock: boom; fallback/mock: boom")

    monkeypatch.setattr(orch, "call_agent_model", fake_fail)

    async def login(client: AsyncClient, email: str, password: str) -> dict:
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await login(client, "admin@example.com", "Admin123!ChangeMe")
        response = await client.post(
            "/api/v1/agent/chat", json={"message": "dữ liệu mới không?"}, headers=admin
        )
        assert response.status_code == 200, response.text
        assert "event: done" in response.text
        assert "truy vấn" in response.text  # template từ evidence

    async with SessionLocal() as db:
        tools = (await db.execute(select(AgentToolCall))).scalars().all()
        assert tools
        assert all(t.duration_ms is not None for t in tools)
        usage = (
            await db.execute(select(AIUsage).where(AIUsage.feature == "agent"))
        ).scalars().all()
        assert usage
        await db.execute(delete(AgentToolCall))
        await db.execute(delete(AIUsage).where(AIUsage.feature == "agent"))
        await db.commit()
