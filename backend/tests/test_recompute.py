import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.performance import PerformanceMetric
from app.models.snapshot import PortfolioSnapshot
from app.models.tier_history import TierHistory
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.services.universe import recompute_universe

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)

PREFIX = "testrecompute"


def _item(pid: str, **overrides):
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    base = {
        "leadPortfolioId": pid,
        "nickname": f"nick-{pid}",
        "portfolioType": "PUBLIC",
        "startTime": now_ms - 200 * 86_400_000,
        "roi": 25.0,
        "pnl": 1000.0,
        "winRate": 55.0,
        "mdd": 10.0,
        "aum": 30000.0,
        "sharpRatio": 1.5,
        "currentCopyCount": 10,
        "maxCopyCount": 200,
        "chartItems": [{"value": 1.0}, {"value": 2.0}],
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
async def _cleanup():
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()
    yield
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()


async def _seed(items):
    async with SessionLocal() as db:
        now = datetime.now(UTC)
        for item in items:
            pid = item["leadPortfolioId"]
            db.add(Trader(lead_portfolio_id=pid, nickname=item["nickname"]))
        await db.flush()
        for item in items:
            pid = item["leadPortfolioId"]
            db.add(
                PortfolioSnapshot(
                    lead_portfolio_id=pid,
                    collected_at=now,
                    collected_hour=now.replace(minute=0, second=0, microsecond=0),
                    source="list",
                    raw=item,
                )
            )
        await db.commit()


@pytest.mark.asyncio
async def test_recompute_assigns_tiers_and_is_idempotent() -> None:
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    weeks = 86_400_000
    await _seed(
        [
            _item(f"{PREFIX}-high"),
            _item(
                f"{PREFIX}-qualified",
                startTime=now_ms - 100 * weeks,
                roi=15.0,
                pnl=500.0,
                winRate=48.0,
                mdd=25.0,
                aum=15000.0,
                sharpRatio=None,
            ),
            _item(f"{PREFIX}-excluded", roi=-5.0),
            _item(
                f"{PREFIX}-watch",
                startTime=now_ms - 60 * weeks,
                roi=5.0,
                mdd=None,
                sharpRatio=None,
            ),
        ]
    )

    async with SessionLocal() as db:
        first = await recompute_universe(db)
        assert first["total"] >= 4
        assert first["counts"].get("high_upper", 0) >= 1
        assert first["counts"].get("qualified_upper", 0) >= 1
        assert first["counts"].get("watch", 0) >= 1
        assert first["counts"].get("excluded", 0) >= 1

        high = await db.get(TraderUniverse, f"{PREFIX}-high")
        qualified = await db.get(TraderUniverse, f"{PREFIX}-qualified")
        assert high is not None and high.potential_tier == "high_upper"
        assert qualified is not None and qualified.potential_tier == "qualified_upper"

        excluded = await db.get(TraderUniverse, f"{PREFIX}-excluded")
        assert excluded is not None
        assert excluded.filter_reasons
        assert "roi_le_0" in excluded.filter_reasons

        watch = await db.get(TraderUniverse, f"{PREFIX}-watch")
        assert watch is not None
        assert watch.pre_score is not None

        history_count = len(
            (
                await db.execute(
                    select(TierHistory).where(
                        TierHistory.lead_portfolio_id.like(f"{PREFIX}%")
                    )
                )
            ).scalars().all()
        )
        assert history_count == 4

        second = await recompute_universe(db)
        assert second["changed"] == 0
        assert second["counts"] == first["counts"]


@pytest.mark.asyncio
async def test_recompute_applies_total_order_demotion() -> None:
    await _seed([_item(f"{PREFIX}-demote")])
    async with SessionLocal() as db:
        db.add(
            PerformanceMetric(
                lead_portfolio_id=f"{PREFIX}-demote",
                time_range="90D",
                collected_at=datetime(2026, 11, 7, 3, 0, tzinfo=UTC),
                total_orders=40,
            )
        )
        await db.commit()

        await recompute_universe(db)
        row = await db.get(TraderUniverse, f"{PREFIX}-demote")
        assert row is not None
        assert row.potential_tier == "qualified_upper"  # high cần >= 100
        assert "total_orders_lt_threshold" in row.filter_reasons
