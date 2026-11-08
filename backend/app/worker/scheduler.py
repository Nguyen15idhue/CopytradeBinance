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


def intervals_from(values: dict[str, int]) -> dict[str, timedelta]:
    return {
        "scan": timedelta(minutes=values["scan_interval_min"]),
        "perf": timedelta(hours=values["deep_interval_hours_watch"]),
        "detail": timedelta(hours=values["deep_interval_hours_qualified"]),
        "trades": timedelta(hours=values["deep_interval_hours_high"]),
        "retention": timedelta(days=1),
    }


def intervals() -> dict[str, timedelta]:
    settings = get_settings()
    return intervals_from(
        {
            "scan_interval_min": settings.scan_interval_min,
            "deep_interval_hours_watch": settings.deep_interval_hours_watch,
            "deep_interval_hours_qualified": settings.deep_interval_hours_qualified,
            "deep_interval_hours_high": settings.deep_interval_hours_high,
        }
    )


async def load_intervals() -> dict[str, timedelta]:
    from app.services.settings_service import get_collector_config

    async with SessionLocal() as db:
        config = await get_collector_config(db)
    return intervals_from(config)


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


async def _run_retention() -> None:
    from app.services.storage.retention import run_retention

    try:
        async with CollectorLock("lock:collector:retention"):
            async with SessionLocal() as db:
                result = await run_retention(db)
                logger.info("retention xong: %s", result)
    except LockUnavailable:
        logger.info("Job retention bỏ qua vì khóa đang được giữ")
    except Exception:  # noqa: BLE001 - không làm chết scheduler
        logger.exception("Job retention thất bại")


async def run_stage(kind: str) -> None:
    if kind == "retention":
        await _run_retention()
        return
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
    current_intervals = await load_intervals()
    last_run = {kind: now for kind in current_intervals}
    last_run.pop("scan", None)  # scan chạy ngay khi khởi động
    logger.info("Scheduler khởi động, interval=%s", current_intervals)
    while True:
        current = datetime.now(UTC)
        current_intervals = await load_intervals()
        for kind in due_jobs(current, last_run, current_intervals):
            last_run[kind] = current
            asyncio.create_task(run_stage(kind))
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
