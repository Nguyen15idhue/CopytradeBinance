"""Scheduler chạy trong container riêng, 1 process (master §12.4).

Quyết định kế hoạch 05: job đến hạn tính từ `collection_logs` (last success),
không dùng `last_run = now` khi khởi động.
"""

import asyncio
import logging
import zlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.collection_log import CollectionLog
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

JOB_LAYERS = {
    "scan": "L0",
    "perf": "L2",
    "detail": "L3",
    "trades": "L4",
}
DEEP_JOBS = {"perf", "detail", "trades"}
RETRY_DELAY = timedelta(minutes=15)
MAX_RETRIES = 3
JITTER_MINUTES = 5
RETENTION_MARKER = "collector:last_retention"


async def _read_retention_marker() -> datetime | None:
    try:
        from redis.asyncio import Redis

        client = Redis.from_url(get_settings().redis_url)
        try:
            raw = await client.get(RETENTION_MARKER)
        finally:
            await client.aclose()
        if not raw:
            return None
        value = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        return datetime.fromisoformat(value)
    except Exception:  # noqa: BLE001 - thiếu marker thì coi như chưa chạy
        return None


async def _write_retention_marker(moment: datetime) -> None:
    try:
        from redis.asyncio import Redis

        client = Redis.from_url(get_settings().redis_url)
        try:
            await client.set(RETENTION_MARKER, moment.isoformat())
        finally:
            await client.aclose()
    except Exception:  # noqa: BLE001
        pass


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


def jitter_for(kind: str) -> timedelta:
    """Jitter ổn định ±5 phút theo từng job (không đổi sau restart)."""
    offset = zlib.crc32(kind.encode("utf-8")) % (JITTER_MINUTES * 2 + 1)
    return timedelta(minutes=offset - JITTER_MINUTES)


def next_due(
    kind: str,
    last_success: datetime | None,
    interval: timedelta,
    retry_at: datetime | None = None,
) -> datetime:
    if last_success is None:
        return datetime.min.replace(tzinfo=UTC)
    due = last_success + interval
    if kind in DEEP_JOBS:
        due += jitter_for(kind)
    if retry_at is not None and retry_at < due:
        return retry_at
    return due


def due_jobs(
    now: datetime,
    last_success: dict[str, datetime | None],
    job_intervals: dict[str, timedelta] | None = None,
    retry_at: dict[str, datetime] | None = None,
) -> list[str]:
    job_intervals = job_intervals or intervals()
    retry_at = retry_at or {}
    return [
        kind
        for kind, gap in job_intervals.items()
        if now >= next_due(kind, last_success.get(kind), gap, retry_at.get(kind))
    ]


async def load_last_success(db) -> dict[str, datetime | None]:
    result: dict[str, datetime | None] = {}
    for kind, layer in JOB_LAYERS.items():
        value = await db.scalar(
            select(func.max(CollectionLog.finished_at)).where(
                CollectionLog.layer == layer,
                CollectionLog.status == "success",
                CollectionLog.detail.is_(None)
                | CollectionLog.detail["test"].is_(None),
            )
        )
        result[kind] = value
    result["retention"] = None
    return result


async def _run_retention() -> None:
    from app.services.storage.retention import run_retention

    try:
        async with CollectorLock("lock:collector:retention"):
            async with SessionLocal() as db:
                result = await run_retention(db)
                logger.info("retention xong: %s", result)
                await _write_retention_marker(datetime.now(UTC))
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
        raise
    finally:
        await adapter.aclose()


async def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    settings = get_settings()
    timeout = timedelta(minutes=settings.collector_job_timeout_min)
    attempts: dict[str, int] = {}
    running: dict[str, asyncio.Task] = {}
    retry_at: dict[str, datetime] = {}

    from app.services.jobs import consume_queue, requeue_orphans

    await requeue_orphans()
    consumer = asyncio.create_task(consume_queue())

    async with SessionLocal() as db:
        last_success = await load_last_success(db)
    last_success["retention"] = await _read_retention_marker()
    logger.info(
        "Scheduler khởi động, interval=%s, last_success=%s",
        await load_intervals(),
        {k: (v.isoformat() if v else None) for k, v in last_success.items()},
    )

    while True:
        now = datetime.now(UTC)
        current_intervals = await load_intervals()
        for kind in due_jobs(now, last_success, current_intervals, retry_at):
            task = running.get(kind)
            if task is not None and not task.done():
                continue
            running[kind] = asyncio.create_task(
                _execute(kind, timeout, attempts, retry_at)
            )

        # Chỉ đọc DB lại khi có job vừa xong để cập nhật last_success.
        for kind, task in list(running.items()):
            if task.done():
                running.pop(kind, None)
                async with SessionLocal() as db:
                    last_success = await load_last_success(db)
                last_success["retention"] = await _read_retention_marker()
        if consumer.done():
            logger.error("Consumer job dừng bất thường, khởi động lại")
            consumer = asyncio.create_task(consume_queue())
        await asyncio.sleep(60)


async def _execute(
    kind: str,
    timeout: timedelta,
    attempts: dict[str, int],
    retry_at: dict[str, datetime],
) -> None:
    try:
        await asyncio.wait_for(run_stage(kind), timeout=timeout.total_seconds())
        attempts[kind] = 0
        retry_at.pop(kind, None)
    except TimeoutError:
        logger.error("Job %s quá timeout %s", kind, timeout)
        attempts[kind] = attempts.get(kind, 0) + 1
        retry_at[kind] = datetime.now(UTC) + RETRY_DELAY
    except LockUnavailable:
        attempts[kind] = attempts.get(kind, 0) + 1
        retry_at[kind] = datetime.now(UTC) + RETRY_DELAY
    except Exception:  # noqa: BLE001
        logger.exception("Job %s thất bại", kind)
        attempts[kind] = attempts.get(kind, 0) + 1
        if attempts[kind] <= MAX_RETRIES:
            retry_at[kind] = datetime.now(UTC) + RETRY_DELAY
        else:
            retry_at.pop(kind, None)


if __name__ == "__main__":
    asyncio.run(main())
