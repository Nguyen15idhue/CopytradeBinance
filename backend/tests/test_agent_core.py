import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.services.agent.model_client import AgentModelResult, parse_tool_protocol
from app.services.agent.verifier import (
    contains_advice,
    extract_trader_ids,
    verify_answer,
)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def test_parse_tool_protocol_json_block() -> None:
    text = '```json\n{"tool_calls": [{"name": "get_data_health", "arguments": {}}]}\n```'
    calls = parse_tool_protocol(text)
    assert len(calls) == 1
    assert calls[0].name == "get_data_health"


def test_parse_tool_protocol_plain_object() -> None:
    calls = parse_tool_protocol('{"tool_calls": [{"name": "sql_query", "arguments": {"q": "x"}}]}')
    assert calls and calls[0].name == "sql_query"
    assert parse_tool_protocol("Xin chào, tôi có thể giúp gì?") == []


def test_advice_detected_vi() -> None:
    assert contains_advice("Bạn nên copy trader này ngay")
    assert not contains_advice("Dữ liệu cho thấy ROI 20%")


def test_verify_numbers_need_evidence() -> None:
    facts = [{"id": "roi_90d", "value": 30.3, "unit": "%"}]
    result = verify_answer("ROI là 30.3% theo dữ liệu.", facts, row_ids=[])
    assert result["unverified_numbers"] == []
    bad = verify_answer("ROI là 99.9% rất cao.", facts, row_ids=[])
    assert bad["unverified_numbers"]


def test_verify_unknown_trader_id() -> None:
    result = verify_answer("Trader 1234567890123456789 rất tốt.", [], row_ids=["111"])
    assert result["unknown_ids"] == ["1234567890123456789"]


def test_extract_trader_ids() -> None:
    assert extract_trader_ids("so sánh 5143921081414022657 và 123") == [
        "5143921081414022657"
    ]


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_agent_chat_rbac_and_sse(monkeypatch) -> None:
    from app.main import app
    from app.seed import seed_admin, seed_viewer

    await seed_admin()
    await seed_viewer()

    async def fake_call(messages, specs, api_key, transport=None, **kwargs):
        return AgentModelResult(text="Chào bạn, dữ liệu collector vẫn mới.", role="primary"), []

    monkeypatch.setattr("app.services.agent.orchestrator.call_agent_model", fake_call)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await _login(client, "admin@example.com", "Admin123!ChangeMe")
        viewer = await _login(client, "viewer@example.com", "Viewer123!ChangeMe")

        forbidden = await client.post(
            "/api/v1/agent/chat", json={"message": "xin chào"}, headers=viewer
        )
        assert forbidden.status_code == 403

        response = await client.post(
            "/api/v1/agent/chat", json={"message": "dữ liệu có mới không?"}, headers=admin
        )
        assert response.status_code == 200, response.text
        body = response.text
        assert "event: done" in body
        assert "event: citation" in body

        sessions = await client.get("/api/v1/agent/sessions", headers=admin)
        assert sessions.status_code == 200
        assert sessions.json()["data"]["items"]


@pytest.mark.asyncio
async def test_agent_multi_turn_memory(monkeypatch) -> None:
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.main import app
    from app.models.agent import AgentMessage, AgentSession
    from app.seed import seed_admin

    await seed_admin()
    seen: list[list[dict]] = []

    async def fake_call(messages, specs, api_key, transport=None, **kwargs):
        seen.append(messages)
        return AgentModelResult(text=f"Trả lời {len(seen)}", role="primary"), []

    monkeypatch.setattr("app.services.agent.orchestrator.call_agent_model", fake_call)

    async def login(client: AsyncClient) -> dict:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin123!ChangeMe"},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin = await login(client)
        first = await client.post(
            "/api/v1/agent/chat", json={"message": "câu hỏi đầu về trader"}, headers=admin
        )
        assert first.status_code == 200
        sid = None
        for line in first.text.splitlines():
            if line.startswith("data:") and "session_id" in line:
                import json as _json

                sid = _json.loads(line[5:])["session_id"]
        assert sid

        second = await client.post(
            "/api/v1/agent/chat",
            json={"message": "còn trader đó thì sao?", "session_id": sid},
            headers=admin,
        )
        assert second.status_code == 200
        # Lượt 2 phải thấy nội dung lượt 1
        turn2_text = " ".join(m.get("content", "") for m in seen[1])
        assert "câu hỏi đầu về trader" in turn2_text
        assert "Trả lời 1" in turn2_text

    async with SessionLocal() as db:
        session = await db.get(AgentSession, sid)
        assert session is not None
        assert "câu hỏi đầu" in (session.title or "")
        count = await db.scalar(
            select(AgentMessage.id).where(AgentMessage.session_id == sid)
        )
        assert count is not None
        rows = (
            await db.execute(
                select(AgentMessage).where(AgentMessage.session_id == sid)
            )
        ).scalars().all()
        assert len(rows) == 4


@pytest.mark.asyncio
async def test_agent_budget_exceeded_blocks() -> None:
    from datetime import date

    from sqlalchemy import delete

    from app.core.database import SessionLocal
    from app.core.errors import ApiError
    from app.models.ai_report import AIUsage
    from app.services.agent.tools import check_agent_budget

    async with SessionLocal() as db:
        await db.execute(delete(AIUsage).where(AIUsage.feature == "agent"))
        db.add(
            AIUsage(
                day=date.today(),
                model="test",
                prompt_tokens=1,
                completion_tokens=1,
                cost_usd=999,
                feature="agent",
            )
        )
        await db.commit()
        try:
            with pytest.raises(ApiError) as exc:
                await check_agent_budget(db, 2.0, 20.0)
            assert exc.value.code == "AGENT_BUDGET_EXCEEDED"
        finally:
            await db.execute(delete(AIUsage).where(AIUsage.feature == "agent"))
            await db.commit()


def test_agent_rate_limit_blocks() -> None:
    from app.core.errors import ApiError
    from app.services.agent.orchestrator import check_rate_limit

    key = "qa-rate-limit-test"
    for _ in range(20):
        check_rate_limit(key, 20)
    with pytest.raises(ApiError) as exc:
        check_rate_limit(key, 20)
    assert exc.value.code == "AGENT_RATE_LIMITED"
