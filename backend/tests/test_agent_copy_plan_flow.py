"""Eval copy_plan qua orchestrator thật, model script hoá (kế hoạch 06, B6.1.5)."""

import os
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from sqlalchemy import select, text

from app.core.database import SessionLocal
from app.models.agent import AgentMessage
from app.models.user import User
from app.services.agent.model_client import AgentModelResult, AgentToolCallRequest
from app.services.agent.orchestrator import _RATE, run_chat, template_from_copy_plan
from app.services.agent.schema import AgentAnswer

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


async def _admin_id() -> Any:
    async with SessionLocal() as db:
        return (
            await db.execute(select(User).where(User.email == "admin@example.com"))
        ).scalars().first().id


async def _trader_with_constraints() -> str:
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text(
                    "SELECT lead_portfolio_id FROM agent_trader_copy_constraints"
                    " WHERE fixed_radio_min_copy_usd IS NOT NULL LIMIT 1"
                )
            )
        ).first()
        assert row is not None
        return row[0]


def _scripted(
    tool_calls: list[AgentToolCallRequest],
    answer: str,
) -> Callable[..., Awaitable[tuple[AgentModelResult, list[str]]]]:
    state = {"step": 0}

    async def fake(messages, specs, api_key, transport=None, **kwargs):
        if state["step"] == 0 and tool_calls:
            state["step"] = 1
            return AgentModelResult(text="", tool_calls=tool_calls), []
        return AgentModelResult(text=answer, role="primary"), []

    return fake


def _event(events, name):
    return next(event for event in events if event.event == name)


def test_agent_answer_includes_copy_plan() -> None:
    answer = AgentAnswer(
        answer="Cấu hình tham chiếu",
        copy_plan={"version": 1, "can_copy": True},
        copy_plan_version=1,
    )
    payload = answer.to_dict()
    assert payload["copy_plan"]["version"] == 1
    assert payload["copy_plan_version"] == 1


def test_template_from_copy_plan_has_fields() -> None:
    text = template_from_copy_plan(
        {
            "copy_mode": {"value": "fixed_amount"},
            "copy_amount_usd": {"value": 24.84},
            "cost_per_order_usd": {"value": 10},
            "total_stop_loss_usd": {"value": 8.69},
            "stop_loss_pct": {"value": 35},
            "take_profit_pct": {"value": None},
            "missing_fields": ["max_slippage_pct"],
        }
    )
    assert "fixed_amount" in text
    assert "24.84" in text
    assert "8.69" in text
    assert "mặc định Binance" in text


@pytest.mark.asyncio
async def test_run_chat_returns_copy_plan(monkeypatch) -> None:
    trader_id = await _trader_with_constraints()
    tool_calls = [
        AgentToolCallRequest(
            name="build_copy_plan",
            arguments={
                "trader_id": trader_id,
                "capital_usd": 100,
                "available_usd": 24.84,
                "risk_policy": "balanced",
            },
        )
    ]
    answer = (
        f"Với {trader_id}, cấu hình tham chiếu dùng fixed_amount, "
        "số tiền 24.84 USDT, tổng cắt lỗ 8.69 USDT. "
        "Thông tin chỉ mang tính tham khảo, không phải lời khuyên đầu tư."
    )
    monkeypatch.setattr(
        "app.services.agent.orchestrator.call_agent_model", _scripted(tool_calls, answer)
    )
    user_id = await _admin_id()
    events = []
    async with SessionLocal() as db:
        async for event in run_chat(db, user_id, "Tôi có 100 USDT, copy trader này thế nào?"):
            events.append(event)
        await db.commit()

    done = _event(events, "done")
    assert done.data["copy_plan"]["trader_id"] == trader_id
    assert done.data["copy_plan_version"] == 1
    assert done.data["copy_plan"]["copy_amount_usd"]["value"] == 24.84

    async with SessionLocal() as db:
        message = await db.get(AgentMessage, done.data["message_id"])
        assert message is not None
        assert message.copy_plan["trader_id"] == trader_id
        assert message.copy_plan_version == 1
