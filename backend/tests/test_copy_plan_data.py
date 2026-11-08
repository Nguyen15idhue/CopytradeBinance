import os

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.services.copy_plan.data import (
    is_tradfi,
    load_copy_context,
    normalize_margin_mode,
    summarize_symbols,
)


def test_normalize_margin_mode() -> None:
    assert normalize_margin_mode("true") == "isolated"
    assert normalize_margin_mode("ISOLATED") == "isolated"
    assert normalize_margin_mode("false") == "cross"
    assert normalize_margin_mode("CROSSED") == "cross"
    assert normalize_margin_mode(None) is None
    assert normalize_margin_mode("unknown") is None


def test_is_tradfi_estimated() -> None:
    assert is_tradfi("XAUUSDT")
    assert is_tradfi("EURUSDT")
    assert not is_tradfi("BTCUSDT")


def test_summarize_symbols_share_and_tradfi() -> None:
    stats = summarize_symbols(
        [
            {"symbol": "BTCUSDT", "cnt": 2, "notional": 600},
            {"symbol": "XAUUSDT", "cnt": 1, "notional": 400},
        ],
        [
            {"symbol": "BTCUSDT", "cnt": 10, "notional": 500},
            {"symbol": "ETHUSDT", "cnt": 5, "notional": 100},
        ],
    )
    top = {item["symbol"]: item for item in stats["top"]}
    assert top["BTCUSDT"]["share_pct"] == 54.55
    assert top["ETHUSDT"]["share_pct"] == 9.09
    assert stats["tradfi"] == ["XAUUSDT"]
    assert stats["tradfi_confidence"] == "estimated"
    assert stats["low_liquidity"] is None


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)
@pytest.mark.asyncio
async def test_load_copy_context_live_trader() -> None:
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
        context = await load_copy_context(db, row[0])
        assert context is not None
        assert context["constraints"]["fixed_radio_min_copy_usd"] is not None
        assert "mdd_90d" in context["metrics"]
        assert "top" in context["symbol_stats"]
        assert context["as_of"]

        missing = await load_copy_context(db, "no-such-trader")
        assert missing is None
