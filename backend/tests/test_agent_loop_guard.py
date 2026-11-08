"""Chống lặp tool: câu hỏi đơn giản không được kết thúc bằng câu trả lời rỗng."""

import os

import pytest
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.agent import AgentToolCall
from app.models.user import User
from app.services.agent.model_client import AgentModelResult, AgentToolCallRequest
from app.services.agent.orchestrator import _RATE, run_chat

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


@pytest.fixture(autouse=True)
async def _reset() -> None:
    _RATE.clear()
    from app.seed import seed_admin

    await seed_admin()
    yield
    _RATE.clear()


async def _admin_id():
    async with SessionLocal() as db:
        return (
            await db.execute(select(User).where(User.email == "admin@example.com"))
        ).scalars().first().id


async def test_repeated_tool_calls_do_not_dead_end(monkeypatch) -> None:
    async def fake(messages, specs, api_key, transport=None, **kwargs):
        return AgentModelResult(
            text="",
            tool_calls=[
                AgentToolCallRequest(
                    "search_knowledge", {"query": "nhóm a b c", "scope": "all"}
                )
            ],
            role="primary",
        ), []

    monkeypatch.setattr("app.services.agent.orchestrator.call_agent_model", fake)
    user_id = await _admin_id()
    events = []
    async with SessionLocal() as db:
        await db.execute(delete(AgentToolCall))
        await db.commit()
        async for event in run_chat(db, user_id, "các nhóm a b c và bị loại là gì"):
            events.append(event)

    done = [event for event in events if event.event == "done"]
    assert done, f"Không có done: {[e.event for e in events]}"
    answer = done[-1].data["answer"]
    assert answer.strip(), "Câu trả lời rỗng"
    assert "Hết 8 bước tool mà chưa có đáp án" not in answer

    warnings = [e.data["message"] for e in events if e.event == "warning"]
    assert any("cùng tham số" in message for message in warnings), warnings

    # Không thực thi lặp: mỗi chữ ký tool chỉ chạy 1 lần.
    async with SessionLocal() as db:
        rows = (await db.execute(select(AgentToolCall))).scalars().all()
    search_rows = [row for row in rows if row.tool_name == "search_knowledge"]
    assert len(search_rows) == 1, len(search_rows)


async def test_empty_model_text_still_answers(monkeypatch) -> None:
    async def fake(messages, specs, api_key, transport=None, **kwargs):
        return AgentModelResult(text="", role="primary"), []

    monkeypatch.setattr("app.services.agent.orchestrator.call_agent_model", fake)
    user_id = await _admin_id()
    events = []
    async with SessionLocal() as db:
        async for event in run_chat(db, user_id, "các nhóm a b c là gì"):
            events.append(event)
    done = [event for event in events if event.event == "done"]
    assert done
    assert done[-1].data["answer"].strip()
