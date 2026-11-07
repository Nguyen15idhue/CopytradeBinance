import os

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.trade import Trade
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.services.collector.base import Page
from app.services.deep_fetch import fetch_full_trades

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)

PREFIX = "testtrades"


class FakeTradeAdapter:
    def __init__(self, sizes: dict[str, int], fail: set[str] | None = None) -> None:
        self.sizes = sizes
        self.fail = fail or set()
        self.calls: list[tuple[str, int]] = []

    async def get_trades(self, portfolio_id: str, page: int) -> Page:
        self.calls.append((portfolio_id, page))
        if portfolio_id in self.fail:
            raise RuntimeError("lỗi giả lập")
        total = self.sizes[portfolio_id]
        start = (page - 1) * 200
        remaining = max(0, total - start)
        count = min(200, remaining)
        items = [
            {
                "time": 1793901928000 + start + offset,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "price": "100",
                "qty": "1",
                "fee": "-0.1",
                "positionSide": "LONG",
            }
            for offset in range(count)
        ]
        return Page(items=items, total=total, page=page)


async def _seed(mapping: dict[str, str]) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()
        for pid, tier in mapping.items():
            db.add(Trader(lead_portfolio_id=pid, nickname=pid))
            db.add(TraderUniverse(lead_portfolio_id=pid, potential_tier=tier, pre_score=50))
        await db.commit()


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()


@pytest.mark.asyncio
async def test_full_trades_fetch_all_pages_and_dedupe() -> None:
    ids = [f"{PREFIX}-high", f"{PREFIX}-qual", f"{PREFIX}-watch"]
    await _seed(
        {
            ids[0]: "high_upper",
            ids[1]: "qualified_upper",
            ids[2]: "watch",
        }
    )
    adapter = FakeTradeAdapter({ids[0]: 450, ids[1]: 200})

    async with SessionLocal() as db:
        first = await fetch_full_trades(
            adapter, db, portfolio_ids=[ids[0], ids[1]]
        )
        assert first["targets"] == 2
        assert first["trades"] == 650
        assert first["errors"] == 0

        stored = await db.scalar(
            select(func.count()).select_from(Trade).where(Trade.lead_portfolio_id.like(f"{PREFIX}%"))
        )
        assert stored == 650

        second = await fetch_full_trades(adapter, db, portfolio_ids=[ids[0], ids[1]])
        assert second["trades"] == 650
        stored_after = await db.scalar(
            select(func.count()).select_from(Trade).where(Trade.lead_portfolio_id.like(f"{PREFIX}%"))
        )
        assert stored_after == 650  # hash chống trùng

        assert (ids[0], 1) in adapter.calls
        assert (ids[0], 3) in adapter.calls  # 450 -> 3 trang, không break sớm
        assert all(pid != ids[2] for pid, _page in adapter.calls)


@pytest.mark.asyncio
async def test_full_trades_error_isolated() -> None:
    ids = [f"{PREFIX}-bad", f"{PREFIX}-good"]
    await _seed({ids[0]: "high_upper", ids[1]: "qualified_upper"})
    adapter = FakeTradeAdapter({ids[0]: 10, ids[1]: 10}, fail={ids[0]})
    async with SessionLocal() as db:
        result = await fetch_full_trades(adapter, db, portfolio_ids=ids)
        assert result["errors"] == 1
        assert result["trades"] == 10
