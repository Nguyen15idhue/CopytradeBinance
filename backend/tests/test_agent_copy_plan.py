import os

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.services.agent.tools import run_tool, tool_specs

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def test_tool_registered() -> None:
    names = {spec["name"] for spec in tool_specs()}
    assert "build_copy_plan" in names


@pytest.mark.asyncio
async def test_build_copy_plan_live_trader() -> None:
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
        trader_id = row[0]
        result = await run_tool(
            db,
            "build_copy_plan",
            {
                "trader_id": trader_id,
                "capital_usd": 100,
                "available_usd": 24.84,
                "risk_policy": "balanced",
            },
        )
        assert result.error is None
        plan = result.data
        assert plan["trader_id"] == trader_id
        assert plan["copy_mode"]["status"] in ("ok", "needs_choice", "blocked")
        assert plan["copy_amount_usd"]["value"] == 24.84
        assert plan["can_copy"] in (True, False, None)
        assert plan["missing_fields"]
        assert result.meta["row_ids"] == [trader_id]
        assert result.meta["limits_version"] == plan["limits_version"]
        assert result.evidence
        evidence_ids = {item.id for item in result.evidence}
        assert plan["evidence_ids"] == [item.id for item in result.evidence]
        assert set(plan["evidence_ids"]) <= evidence_ids


@pytest.mark.asyncio
async def test_build_copy_plan_20usd_complete() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db,
            "build_copy_plan",
            {
                "trader_id": "5235238076957499648",
                "capital_usd": 20,
                "available_usd": 20,
                "risk_policy": "balanced",
            },
        )
        assert result.error is None
        plan = result.data
        assert plan["copy_mode"]["value"] == "fixed_ratio"
        assert plan["copy_mode"]["auto_selected"] is True
        assert plan["copy_amount_usd"]["value"] == 20.0
        assert plan["stop_loss_pct"]["value"] == 12.0
        assert plan["total_stop_loss_usd"]["value"] == 2.37
        assert plan["max_slippage_pct"]["value"] == 0.5
        assert plan["take_profit_pct"]["status"] == "defaulted"
        assert plan["missing_fields"] == []


@pytest.mark.asyncio
async def test_build_copy_plan_missing_trader() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db, "build_copy_plan", {"trader_id": "no-such-trader", "capital_usd": 100}
        )
        assert result.error is not None


@pytest.mark.asyncio
async def test_build_copy_plan_rejects_bad_capital() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db, "build_copy_plan", {"trader_id": "x", "capital_usd": 0}
        )
        assert result.error is not None
