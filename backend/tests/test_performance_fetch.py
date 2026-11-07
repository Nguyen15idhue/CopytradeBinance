import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.performance import PerformanceMetric
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.services.deep_fetch import fetch_performance_for_watch

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)

PREFIX = "testperf"


class FakePerformanceAdapter:
    def __init__(self, total_orders: dict[str, int], fail: set[str] | None = None) -> None:
        self.total_orders = total_orders
        self.fail = fail or set()
        self.calls: list[str] = []

    async def get_performance(self, portfolio_id: str, time_range: str) -> dict:
        self.calls.append(portfolio_id)
        if portfolio_id in self.fail:
            raise RuntimeError("lỗi giả lập")
        return {
            "timeRange": time_range,
            "roi": 12.5,
            "pnl": 100.0,
            "mdd": None if time_range == "7D" else 8.5,
            "copierPnl": 0.0,
            "winRate": 55.0,
            "winOrders": 5,
            "totalOrder": self.total_orders[portfolio_id],
            "sharpRatio": None,
        }


async def _seed_tiers(mapping: dict[str, str]) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()
        for pid, tier in mapping.items():
            db.add(Trader(lead_portfolio_id=pid, nickname=pid))
            db.add(TraderUniverse(lead_portfolio_id=pid, potential_tier=tier))
        await db.commit()


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()


@pytest.mark.asyncio
async def test_performance_saved_and_tier_demoted() -> None:
    await _seed_tiers(
        {
            f"{PREFIX}-high": "high_upper",
            f"{PREFIX}-qual": "qualified_upper",
            f"{PREFIX}-watch": "watch",
        }
    )
    adapter = FakePerformanceAdapter(
        {f"{PREFIX}-high": 40, f"{PREFIX}-qual": 60, f"{PREFIX}-watch": 10}
    )
    moment = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)

    async with SessionLocal() as db:
        first = await fetch_performance_for_watch(
            adapter,
            db,
            collected_at=moment,
            portfolio_ids=[
                f"{PREFIX}-high",
                f"{PREFIX}-qual",
                f"{PREFIX}-watch",
            ],
        )
        assert first["traders"] == 3
        assert first["metrics_saved"] == 12
        assert first["demotions"] == 1  # high 40 < 100 → qualified

        high = await db.get(TraderUniverse, f"{PREFIX}-high")
        qual = await db.get(TraderUniverse, f"{PREFIX}-qual")
        assert high is not None and high.potential_tier == "qualified_upper"
        assert qual is not None and qual.potential_tier == "qualified_upper"

        count = await db.scalar(
            select(func.count())
            .select_from(PerformanceMetric)
            .where(PerformanceMetric.lead_portfolio_id.like(f"{PREFIX}%"))
        )
        assert count == 12

        seventh = await db.scalar(
            select(PerformanceMetric.mdd).where(
                PerformanceMetric.lead_portfolio_id == f"{PREFIX}-qual",
                PerformanceMetric.time_range == "7D",
                PerformanceMetric.collected_at == moment,
            )
        )
        assert seventh is None  # mdd null giữ null

        second = await fetch_performance_for_watch(
            adapter,
            db,
            collected_at=moment,
            portfolio_ids=[
                f"{PREFIX}-high",
                f"{PREFIX}-qual",
                f"{PREFIX}-watch",
            ],
        )
        assert second["metrics_saved"] == 12
        count_after = await db.scalar(
            select(func.count())
            .select_from(PerformanceMetric)
            .where(PerformanceMetric.lead_portfolio_id.like(f"{PREFIX}%"))
        )
        assert count_after == 12  # cùng giờ → upsert, không nhân bản


@pytest.mark.asyncio
async def test_excluded_trader_never_targeted() -> None:
    await _seed_tiers(
        {f"{PREFIX}-excluded": "excluded", f"{PREFIX}-watch": "watch"}
    )
    adapter = FakePerformanceAdapter(
        {f"{PREFIX}-excluded": 100, f"{PREFIX}-watch": 100}
    )
    async with SessionLocal() as db:
        result = await fetch_performance_for_watch(
            adapter,
            db,
            portfolio_ids=[f"{PREFIX}-excluded", f"{PREFIX}-watch"],
        )
        assert result["targets"] == 1
        assert all(call == f"{PREFIX}-watch" for call in adapter.calls)


@pytest.mark.asyncio
async def test_performance_errors_do_not_crash() -> None:
    await _seed_tiers({f"{PREFIX}-bad": "qualified_upper", f"{PREFIX}-good": "watch"})
    adapter = FakePerformanceAdapter(
        {f"{PREFIX}-bad": 60, f"{PREFIX}-good": 30}, fail={f"{PREFIX}-bad"}
    )
    async with SessionLocal() as db:
        result = await fetch_performance_for_watch(
            adapter, db, portfolio_ids=[f"{PREFIX}-bad", f"{PREFIX}-good"]
        )
        assert result["errors"] == 4
        assert result["traders"] == 1
