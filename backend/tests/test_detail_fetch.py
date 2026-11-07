import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.position import Position
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.models.transfer import Transfer
from app.models.universe import TraderUniverse
from app.services.collector.base import Page
from app.services.deep_fetch import fetch_detail_and_history

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)

PREFIX = "testdetail"


class FakeDetailAdapter:
    def __init__(self, paused: set[str] | None = None, full_slots: set[str] | None = None) -> None:
        self.paused = paused or set()
        self.full_slots = full_slots or set()
        self.position_calls: list[str] = []

    async def get_detail(self, portfolio_id: str) -> dict:
        return {
            "status": "ACTIVE",
            "isPaused": portfolio_id in self.paused,
            "nickname": f"nick-{portfolio_id}",
            "portfolioType": "PUBLIC",
            "positionShow": False,
            "currentCopyCount": 100 if portfolio_id in self.full_slots else 5,
            "maxCopyCount": 100,
            "startTime": 1700000000000,
            "lastTradeTime": 1793901928000,
            "futuresType": "UM",
            "initInvestAsset": "USDT",
        }

    async def get_positions(self, portfolio_id: str, page: int) -> Page:
        self.position_calls.append(portfolio_id)
        if page == 1:
            return Page(
                items=[
                    {
                        "positionId": f"{portfolio_id}-p1",
                        "symbol": "BTCUSDT",
                        "side": "Long",
                        "leverage": 10,
                        "closingPnl": "12.5",
                    }
                ],
                total=2,
                page=1,
            )
        return Page(
            items=[{"positionId": f"{portfolio_id}-p2", "symbol": "ETHUSDT", "side": "Short"}],
            total=2,
            page=2,
        )

    async def get_transfers(self, portfolio_id: str, page: int) -> Page:
        return Page(
            items=[
                {
                    "time": 1793903160000,
                    "coin": "USDT",
                    "amount": "1000",
                    "from": "Fiat and Spot",
                    "to": "Lead Trading Account",
                    "transType": "LEAD_DEPOSIT",
                }
            ],
            total=1,
            page=page,
        )


async def _seed(mapping: dict[str, str]) -> None:
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
async def test_detail_positions_transfers_and_eligibility() -> None:
    ids = [f"{PREFIX}-ok", f"{PREFIX}-paused", f"{PREFIX}-full"]
    await _seed(
        {
            ids[0]: "qualified_upper",
            ids[1]: "qualified_upper",
            ids[2]: "high_upper",
        }
    )
    adapter = FakeDetailAdapter(paused={ids[1]}, full_slots={ids[2]})
    moment = datetime(2026, 11, 7, 10, 0, tzinfo=UTC)

    async with SessionLocal() as db:
        first = await fetch_detail_and_history(
            adapter, db, collected_at=moment, portfolio_ids=ids
        )
        assert first["detail_ok"] == 3
        assert first["ineligible"] == 2
        assert first["history_targets"] == 1
        assert first["positions"] == 2
        assert first["transfers"] == 1
        assert set(adapter.position_calls) == {ids[0]}  # positionShow=false vẫn gọi
        assert len(adapter.position_calls) == 2  # đủ 2 trang

        trader = await db.get(Trader, ids[0])
        assert trader is not None and trader.status == "ACTIVE"
        assert trader.last_trade_time is not None

        snapshots = await db.scalar(
            select(func.count())
            .select_from(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.lead_portfolio_id == ids[0],
                PortfolioSnapshot.source == "detail",
            )
        )
        assert snapshots == 1

        positions = await db.scalar(
            select(func.count())
            .select_from(Position)
            .where(Position.lead_portfolio_id == ids[0])
        )
        assert positions == 2
        transfers = await db.scalar(
            select(func.count())
            .select_from(Transfer)
            .where(Transfer.lead_portfolio_id == ids[0])
        )
        assert transfers == 1

        second = await fetch_detail_and_history(
            adapter, db, collected_at=moment, portfolio_ids=ids
        )
        assert second["positions"] == 2
        positions_after = await db.scalar(
            select(func.count())
            .select_from(Position)
            .where(Position.lead_portfolio_id == ids[0])
        )
        assert positions_after == 2  # hash/unique chống trùng
