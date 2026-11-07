"""Job registry trong process cho các thao tác collector."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.database import SessionLocal
from app.services.collector.binance import BinanceBapiAdapter
from app.services.collector.lock import CollectorLock, LockUnavailable
from app.services.config_store import collector_enabled

JOBS: dict[str, dict[str, Any]] = {}
MAX_JOBS = 20


def _create_job(kind: str) -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "id": job_id,
        "kind": kind,
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "result": None,
        "error": None,
    }
    if len(JOBS) > MAX_JOBS:
        for key in list(JOBS)[:-MAX_JOBS]:
            JOBS.pop(key, None)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return JOBS.get(job_id)


def recent_jobs(limit: int = 10) -> list[dict[str, Any]]:
    return list(JOBS.values())[-limit:]


def start_scan_job() -> str:
    job_id = _create_job("scan")
    asyncio.create_task(_run_scan(job_id))
    return job_id


def start_deep_job() -> str:
    job_id = _create_job("deep")
    asyncio.create_task(_run_deep(job_id))
    return job_id


async def _run_scan(job_id: str) -> None:
    job = JOBS[job_id]
    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:scan"):
            async with SessionLocal() as db:
                if not await collector_enabled(db):
                    job["status"] = "skipped"
                    job["result"] = {"reason": "kill_switch"}
                    return
                from app.services.universe import recompute_universe, scan_universe

                scan = await scan_universe(adapter, db)
                tiering = await recompute_universe(db)
                job["result"] = {"scan": scan.as_dict(), "tiering": tiering}
        job["status"] = "success"
    except LockUnavailable as exc:
        job["status"] = "skipped"
        job["result"] = {"reason": str(exc)}
    except Exception as exc:  # noqa: BLE001
        job["status"] = "failed"
        job["error"] = str(exc)
    finally:
        job["finished_at"] = datetime.now(UTC).isoformat()
        await adapter.aclose()


async def _run_deep(job_id: str) -> None:
    job = JOBS[job_id]
    adapter = BinanceBapiAdapter()
    try:
        async with CollectorLock("lock:collector:deep"):
            async with SessionLocal() as db:
                if not await collector_enabled(db):
                    job["status"] = "skipped"
                    job["result"] = {"reason": "kill_switch"}
                    return
                from app.services.deep_fetch import (
                    fetch_detail_and_history,
                    fetch_full_trades,
                    fetch_performance_for_watch,
                )

                perf = await fetch_performance_for_watch(adapter, db)
                detail = await fetch_detail_and_history(adapter, db)
                trades = await fetch_full_trades(adapter, db)
                job["result"] = {"performance": perf, "detail": detail, "trades": trades}
        job["status"] = "success"
    except LockUnavailable as exc:
        job["status"] = "skipped"
        job["result"] = {"reason": str(exc)}
    except Exception as exc:  # noqa: BLE001
        job["status"] = "failed"
        job["error"] = str(exc)
    finally:
        job["finished_at"] = datetime.now(UTC).isoformat()
        await adapter.aclose()
