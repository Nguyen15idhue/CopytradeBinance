import os

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.trader_metric import TraderMetric
from app.services.agent.db_tools import (  # noqa: F401 - đăng ký tool
    compare_traders,
    get_ranking,
    get_risk_events,
    get_trader_profile,
    search_traders,
)
from app.services.agent.tools import get_data_health, run_tool

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


async def _any_trader_id() -> str:
    async with SessionLocal() as db:
        row = await db.execute(select(TraderMetric.lead_portfolio_id).limit(1))
        return str(row.scalars().first())


@pytest.mark.asyncio
async def test_search_top_safe_deterministic() -> None:
    policy = {
        "risk_level": ["low", "none"],
        "min_runtime_days": 90,
        "max_mdd_90d": 20,
        "max_leverage": 5,
        "sort": [{"field": "score", "dir": "desc"}],
        "limit": 10,
    }
    async with SessionLocal() as db:
        first = await search_traders(db, policy)
        assert first.error is None
        assert len(first.data["items"]) <= 10
        assert first.meta["row_ids"] == [item["id"] for item in first.data["items"]]
        if first.data["items"]:
            assert first.evidence
        second = await search_traders(db, policy)
        assert [i["id"] for i in second.data["items"]] == [
            i["id"] for i in first.data["items"]
        ]


@pytest.mark.asyncio
async def test_search_risk_score_filter_and_empty_case() -> None:
    async with SessionLocal() as db:
        result = await search_traders(db, {"risk_score_max": 40, "limit": 10})
        assert result.error is None
        for item in result.data["items"]:
            assert item["risk_score"] is not None and item["risk_score"] <= 40

        # Không có trader nào risk_score <= -1 → rỗng nhưng vẫn có cấu trúc.
        empty = await search_traders(db, {"risk_score_max": -1, "limit": 10})
        assert empty.error is None
        assert empty.data["items"] == []
        assert empty.meta["row_ids"] == []


@pytest.mark.asyncio
async def test_profile_full_payload_and_windows() -> None:
    trader_id = await _any_trader_id()
    async with SessionLocal() as db:
        full = await get_trader_profile(db, {"trader_id": trader_id, "detail": "full"})
        assert full.error is None
        windows = full.data["windows"]
        assert set(windows) == {"7D", "30D", "90D", "180D"}
        for window in windows.values():
            assert set(window) == {
                "roi", "pnl", "mdd", "sharpe", "copier_pnl",
                "win_rate_order", "win_orders", "total_orders",
            }
        assert full.data["derived"]
        assert set(full.data["profile"]) == {
            "aum", "copy_aum", "current_copiers", "max_copiers", "total_copiers",
            "profit_sharing_rate", "margin_balance", "favorite_count",
            "portfolio_type", "status",
        }
        assert "breakdown" in full.data
        assert "flags" in full.data
        assert "data_quality" in full.data
        assert "symbol_stats" in full.data
        labels = {item.id for item in full.evidence}
        assert f"{trader_id}:roi_7d" in labels
        assert f"{trader_id}:roi_180d" in labels
        assert f"{trader_id}:data_reliability_score" in labels

        summary = await get_trader_profile(
            db, {"trader_id": trader_id, "detail": "summary"}
        )
        assert summary.error is None
        assert summary.data["derived"] == {}
        assert summary.data["profile"] == {}
        assert summary.data["windows"]["7D"]["roi"] == windows["7D"]["roi"]


@pytest.mark.asyncio
async def test_profile_flags_mdd_suspect_and_missing_trades() -> None:
    trader_id = "5235238076957499648"
    async with SessionLocal() as db:
        profile = await get_trader_profile(db, {"trader_id": trader_id})
        assert profile.error is None
        quality = profile.data["data_quality"]
        assert quality["mdd_suspect"] is True
        assert quality["missing_trades"] is True
        assert quality["trade_count"] == 0
        assert quality["position_count"] > 0
        assert quality["reliability_score"] is not None
        assert profile.data["derived"]["active_days"] is None
        assert profile.data["derived"]["total_fills"] is None
        assert profile.data["symbol_stats"]["top"]
        assert any("MDD" in note for note in quality["notes"])

        fit = await run_tool(
            db,
            "analyze_portfolio_fit",
            {"trader_id": trader_id, "capital_usd": 20},
        )
        assert fit.error is None
        assert fit.data["data_quality"]["mdd_suspect"] is True
        assert any("MDD" in warning for warning in fit.data["warnings"])
        assert fit.data["risk"]["level"] in ("high", "critical")


@pytest.mark.asyncio
async def test_search_returns_windows_and_copier_fields() -> None:
    async with SessionLocal() as db:
        result = await search_traders(db, {"min_copiers": 1, "limit": 3})
        assert result.error is None
        assert result.data["items"]
        item = result.data["items"][0]
        assert set(item["windows"]) == {"7D", "30D", "90D", "180D"}
        assert "current_copiers" in item
        assert "copier_pnl_90d" in item
        labels = {e.id for e in result.evidence}
        assert any(label.endswith(":roi_7d") for label in labels)


@pytest.mark.asyncio
async def test_search_limit_capped_and_structured() -> None:
    async with SessionLocal() as db:
        result = await search_traders(db, {"limit": 500})
        assert result.error is None
        assert len(result.data["items"]) <= 50


@pytest.mark.asyncio
async def test_profile_compare_ranking_risk() -> None:
    trader_id = await _any_trader_id()
    async with SessionLocal() as db:
        profile = await get_trader_profile(db, {"trader_id": trader_id})
        assert profile.error is None
        assert profile.data["id"] == trader_id
        assert profile.meta["row_ids"] == [trader_id]
        assert "current_copiers" in profile.data
        assert "copier_pnl_90d" in profile.data

        unknown = await get_trader_profile(db, {"trader_id": "no-such-trader"})
        assert unknown.error is not None
        assert unknown.data is None

        rows = await db.execute(
            select(TraderMetric.lead_portfolio_id)
            .where(TraderMetric.lead_portfolio_id != trader_id)
            .limit(1)
        )
        other = str(rows.scalars().first() or trader_id)
        compared = await compare_traders(db, {"trader_ids": [trader_id, other]})
        assert compared.error is None

        few = await compare_traders(db, {"trader_ids": [trader_id]})
        assert few.error is not None

        ranking = await run_tool(db, "get_ranking", {"board": "overall", "top_n": 5})
        assert ranking.error is None or "snapshot" in (ranking.error or "")

        events = await get_risk_events(db, {"trader_id": trader_id, "limit": 5})
        assert events.error is None

        health = await get_data_health(db, {})
        assert health.error is None
        assert "recent_runs" in health.data
