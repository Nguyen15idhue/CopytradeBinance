"""Job collector lưu DB + hàng đợi Redis (kế hoạch 05, bước 5.0.6).

DB là nguồn sự thật; Redis chỉ là hàng đợi tín hiệu cho worker.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.collector_job import CollectorJob
from app.services.collector.binance import BinanceBapiAdapter
from app.services.collector.lock import CollectorLock, LockUnavailable
from app.services.config_store import collector_enabled

logger = logging.getLogger(__name__)

QUEUE_KEY = "queue:collector:jobs"
KINDS = ("scan", "deep")


async def _redis():
    from redis.asyncio import Redis

    return Redis.from_url(get_settings().redis_url)


async def enqueue_job(job_id: UUID) -> None:
    client = await _redis()
    try:
        await client.lpush(QUEUE_KEY, str(job_id))
    finally:
        await client.aclose()


async def create_job(
    db: AsyncSession, kind: str, requested_by: UUID | None
) -> CollectorJob:
    if kind not in KINDS:
        raise ValueError(f"kind không hợp lệ: {kind}")
    job = CollectorJob(id=uuid4(), kind=kind, status="queued", requested_by=requested_by)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: UUID) -> CollectorJob | None:
    return await db.get(CollectorJob, job_id)


async def list_jobs(db: AsyncSession, limit: int = 10) -> list[CollectorJob]:
    rows = (
        await db.execute(
            select(CollectorJob).order_by(CollectorJob.requested_at.desc()).limit(limit)
        )
    ).scalars().all()
    return list(rows)


async def recent_jobs(db: AsyncSession, limit: int = 10) -> list[dict[str, Any]]:
    return [job.as_dict() for job in await list_jobs(db, limit)]


async def _update(
    job_id: UUID,
    status: str | None = None,
    result: dict | None = None,
    error: str | None = None,
    started: bool = False,
    finished: bool = False,
) -> None:
    async with SessionLocal() as db:
        job = await db.get(CollectorJob, job_id)
        if job is None:
            return
        if status is not None:
            job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error[:1000]
        if started:
            job.started_at = datetime.now(UTC)
        if finished:
            job.finished_at = datetime.now(UTC)
        await db.commit()


async def run_job(job_id: UUID) -> None:
    """Chạy một job đã có trong DB (worker consume hàng đợi gọi hàm này)."""
    async with SessionLocal() as db:
        job = await db.get(CollectorJob, job_id)
        if job is None:
            logger.warning("Job %s không tồn tại", job_id)
            return
        if job.status in ("success", "failed", "skipped"):
            return
        kind = job.kind
        if not await collector_enabled(db):
            await _update(job_id, status="skipped", result={"reason": "kill_switch"},
                          started=True, finished=True)
            return
        await _update(job_id, status="running", started=True)

    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:scan" if kind == "scan"
                                 else "lock:collector:deep"):
            async with SessionLocal() as db:
                if not await collector_enabled(db):
                    await _update(job_id, status="skipped",
                                  result={"reason": "kill_switch"}, finished=True)
                    return
                if kind == "scan":
                    from app.services.universe import recompute_universe, scan_universe

                    scan = await scan_universe(adapter, db)
                    tiering = await recompute_universe(db)
                    result = {"scan": scan.as_dict(), "tiering": tiering}
                else:
                    from app.services.deep_fetch import (
                        fetch_detail_and_history,
                        fetch_full_trades,
                        fetch_performance_for_watch,
                    )

                    perf = await fetch_performance_for_watch(adapter, db)
                    detail = await fetch_detail_and_history(adapter, db)
                    trades = await fetch_full_trades(adapter, db)
                    result = {"performance": perf, "detail": detail, "trades": trades}
        await _update(job_id, status="success", result=result, finished=True)
    except LockUnavailable as exc:
        await _update(job_id, status="skipped", result={"reason": str(exc)},
                      finished=True)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s thất bại", job_id)
        await _update(job_id, status="failed", error=str(exc), finished=True)
    finally:
        await adapter.aclose()


async def consume_queue(stop: Any = None) -> None:
    """Worker: lấy job từ Redis, chạy tuần tự."""
    import asyncio

    client = await _redis()
    try:
        while stop is None or not stop.is_set():
            try:
                item = await client.brpop(QUEUE_KEY, timeout=5)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - Redis lỗi thì thử lại
                await asyncio.sleep(5)
                continue
            if not item:
                await asyncio.sleep(1)
                continue
            _key, raw = item
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            try:
                job_id = UUID(str(raw).strip())
            except (TypeError, ValueError, AttributeError):
                logger.warning("Bỏ qua job id không hợp lệ: %s", raw)
                continue
            await run_job(job_id)
    finally:
        await client.aclose()


async def requeue_orphans() -> int:
    """Đưa job queued/running còn kẹt trở lại hàng đợi sau restart."""
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(CollectorJob).where(
                    CollectorJob.status.in_(("queued", "running"))
                )
            )
        ).scalars().all()
        for job in rows:
            job.status = "queued"
            job.started_at = None
        await db.commit()
        count = len(rows)
    client = await _redis()
    try:
        for job in rows:
            await client.lpush(QUEUE_KEY, str(job.id))
    finally:
        await client.aclose()
    return count


def dump(job: CollectorJob) -> str:
    return json.dumps(job.as_dict(), ensure_ascii=False, default=str)
