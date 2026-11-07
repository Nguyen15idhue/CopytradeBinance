"""Scheduler chạy trong container riêng, 1 process (master §12.4)."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.collector.binance import BinanceBapiAdapter
from app.services.collector.lock import CollectorLock, LockUnavailable
from app.services.config_store import collector_enabled
from app.services.deep_fetch import (
    fetch_detail_and_history,
    fetch_full_trades,
    fetch_performance_for_watch,
)
from app.services.universe import recompute_universe, scan_universe

logger = logging.getLogger(__name__)


def intervals() -> dict[str, timedelta]:
    settings = get_settings()
    return {
        "scan": timedelta(minutes=settings.scan_interval_min),
        "perf": timedelta(hours=settings.deep_interval_hours_watch),
        "detail": timedelta(hours=settings.deep_interval_hours_qualified),
        "trades": timedelta(hours=settings.deep_interval_hours_high),
    }


def due_jobs(
    now: datetime,
    last_run: dict[str, datetime],
    job_intervals: dict[str, timedelta] | None = None,
) -> list[str]:
    job_intervals = job_intervals or intervals()
    return [
        kind
        for kind, gap in job_intervals.items()
        if kind not in last_run or now - last_run[kind] >= gap
    ]


async def run_stage(kind: str) -> None:
    lock_key = "lock:collector:scan" if kind == "scan" else "lock:collector:deep"
    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock(lock_key):
            async with SessionLocal() as db:
                if not await collector_enabled(db):
                    logger.info("Kill switch bật, bỏ qua job %s", kind)
                    return
                if kind == "scan":
                    result = await scan_universe(adapter, db)
                    tiering = await recompute_universe(db)
                    logger.info("scan xong: %s | tiering: %s", result.as_dict(), tiering)
                elif kind == "perf":
                    logger.info("perf xong: %s", await fetch_performance_for_watch(adapter, db))
                elif kind == "detail":
                    logger.info("detail xong: %s", await fetch_detail_and_history(adapter, db))
                elif kind == "trades":
                    logger.info("trades xong: %s", await fetch_full_trades(adapter, db))
    except LockUnavailable:
        logger.warning("Job %s bỏ qua vì khóa đang được giữ", kind)
    except Exception:  # noqa: BLE001
        logger.exception("Job %s thất bại", kind)
    finally:
        await adapter.aclose()


async def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    now = datetime.now(UTC)
    last_run = {kind: now for kind in intervals()}  # deep chờ đủ interval
    last_run.pop("scan", None)  # scan chạy ngay khi khởi động
    logger.info("Scheduler khởi động, interval=%s", intervals())
    while True:
        current = datetime.now(UTC)
        for kind in due_jobs(current, last_run):
            last_run[kind] = current
            asyncio.create_task(run_stage(kind))
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
