import os

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.services.agent.portfolio import analyze_portfolio_fit, evaluate_fit

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def _constraints(min_copy: float | None = 10.0) -> dict:
    return {
        "fixed_radio_min_copy_usd": min_copy,
        "fixed_amount_min_copy_usd": min_copy,
    }


def _metrics() -> dict:
    return {"mdd_90d": 20.0, "worst_position_roi": -10.0,
            "max_leverage": 5.0, "risk_level": "low", "risk_score": 30.0}


def test_below_min_cannot_copy() -> None:
    fit = evaluate_fit(_constraints(100.0), _metrics(), 99.0)
    assert fit["can_copy"] is False
    assert fit["capital_ok"] is False
    assert fit["min_copy_usd"] == 100.0


def test_equal_min_can_copy() -> None:
    fit = evaluate_fit(_constraints(100.0), _metrics(), 100.0)
    assert fit["can_copy"] is True
    assert fit["max_loss_at_mdd_usd"] == 20.0


def test_above_min_with_loss_estimate() -> None:
    fit = evaluate_fit(_constraints(10.0), _metrics(), 100.0)
    assert fit["can_copy"] is True
    assert fit["worst_position_loss_usd"] == -10.0


def test_missing_fields_unknown() -> None:
    fit = evaluate_fit({}, {"mdd_90d": None, "risk_level": None, "risk_score": None}, 100.0)
    assert fit["can_copy"] == "unknown"
    assert "min_copy_usd" in fit["missing_fields"]
    assert "max_loss_at_mdd_usd" in fit["missing_fields"]


@pytest.mark.asyncio
async def test_portfolio_fit_live_trader() -> None:
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text("SELECT lead_portfolio_id FROM agent_trader_copy_constraints"
                     " WHERE fixed_radio_min_copy_usd IS NOT NULL LIMIT 1")
            )
        ).first()
        assert row is not None
        trader_id = row[0]
        result = await analyze_portfolio_fit(
            db, {"trader_id": trader_id, "capital_usd": 100}
        )
        assert result.error is None
        assert result.data["trader_id"] == trader_id
        assert result.data["capital_usd"] == 100
        assert result.meta["row_ids"] == [trader_id]

        missing = await analyze_portfolio_fit(db, {"trader_id": "no-such", "capital_usd": 100})
        assert missing.error is not None
