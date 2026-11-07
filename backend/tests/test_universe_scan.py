import os
import tempfile

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.collection_log import CollectionLog
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.services.collector.base import Page
from app.services.collector.lock import CollectorLock, LockUnavailable
from app.services.storage.raw import RawArchive
from app.services.universe import dedupe, scan_universe

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL + Redis trong compose",
)

PREFIX = "testscan"


class FakeListAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str]] = []

    async def list_traders(
        self, time_range: str, page: int, portfolio_type: str = "PUBLIC"
    ) -> Page:
        self.calls.append((time_range, page, portfolio_type))
        if portfolio_type == "PUBLIC":
            pages = {
                1: [f"{PREFIX}-1", f"{PREFIX}-2"],
                2: [f"{PREFIX}-3"],
                3: [f"{PREFIX}-3"],  # trùng trong cùng loại
            }
            items = pages.get(page)
            return Page(items=[{"leadPortfolioId": pid} for pid in items or []], total=3, page=page)
        pages = {1: [f"{PREFIX}-1", f"{PREFIX}-4"]}  # trùng với PUBLIC
        items = pages.get(page)
        return Page(items=[{"leadPortfolioId": pid} for pid in items or []], total=2, page=page)


def test_dedupe_keeps_first_and_counts_duplicates() -> None:
    items = [{"leadPortfolioId": "a"}, {"leadPortfolioId": "b"}, {"leadPortfolioId": "a"}]
    unique, duplicates = dedupe(items)
    assert [item["leadPortfolioId"] for item in unique] == ["a", "b"]
    assert duplicates == 1


@pytest.mark.asyncio
async def test_lock_blocks_second_holder() -> None:
    async with CollectorLock("lock:test:collector", ttl_seconds=30):
        with pytest.raises(LockUnavailable):
            async with CollectorLock("lock:test:collector", ttl_seconds=30):
                pass


@pytest.mark.asyncio
async def test_scan_dedupes_and_is_idempotent() -> None:
    adapter = FakeListAdapter()
    archive = RawArchive(tempfile.mkdtemp(prefix="raw-scan-"))
    async with SessionLocal() as db:
        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()

        first = await scan_universe(adapter, db, archive=archive)
        assert first.total == 4
        assert first.duplicates == 1
        assert first.pages == 3
        assert first.by_type == {"PUBLIC": 3, "SIGNAL": 1}

        second = await scan_universe(adapter, db, archive=archive)
        assert second.total == 4

        traders = await db.scalar(
            select(func.count()).select_from(Trader).where(
                Trader.lead_portfolio_id.like(f"{PREFIX}%")
            )
        )
        snapshots = await db.scalar(
            select(func.count()).select_from(PortfolioSnapshot).where(
                PortfolioSnapshot.lead_portfolio_id.like(f"{PREFIX}%")
            )
        )
        assert traders == 4
        assert snapshots == 4

        logs = (
            await db.execute(
                select(CollectionLog)
                .where(CollectionLog.layer == "L0")
                .order_by(CollectionLog.id.desc())
                .limit(2)
            )
        ).scalars().all()
        assert logs[0].status == "success"
        assert logs[0].detail["total"] == 4

        await db.execute(delete(Trader).where(Trader.lead_portfolio_id.like(f"{PREFIX}%")))
        await db.commit()
