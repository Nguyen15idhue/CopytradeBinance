from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.collection_log import CollectionLog
from app.models.universe import TraderUniverse
from app.models.user import User
from app.services.config_store import KILL_SWITCH_KEY, collector_enabled, set_setting
from app.services.jobs import get_job, recent_jobs, start_deep_job, start_scan_job
from app.services.storage.raw import RawArchive

router = APIRouter(prefix="/collector", tags=["collector"])

LAYERS = ("L0", "L2", "L3", "L4")


class KillSwitchRequest(BaseModel):
    active: bool


@router.get("/status")
async def status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for layer in LAYERS:
        row = (
            await db.execute(
                select(CollectionLog)
                .where(CollectionLog.layer == layer)
                .order_by(CollectionLog.id.desc())
                .limit(1)
            )
        ).scalars().first()
        latest[layer] = (
            None
            if row is None
            else {
                "status": row.status,
                "started_at": row.started_at.isoformat(),
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "requests": row.requests,
                "items_ok": row.items_ok,
                "error_count": row.error_count,
                "detail": row.detail,
            }
        )

    tiers = dict(
        (
            await db.execute(
                select(TraderUniverse.potential_tier, func.count()).group_by(
                    TraderUniverse.potential_tier
                )
            )
        ).all()
    )
    archive = await RawArchive().manifest_stats(db)
    return ok(
        {
            "enabled": await collector_enabled(db),
            "kill_switch_key": KILL_SWITCH_KEY,
            "tiers": tiers,
            "latest_runs": latest,
            "jobs": recent_jobs(),
            "raw_archive": archive,
            "generated_at": datetime.now(UTC).isoformat(),
        },
        request,
    )


@router.post("/run-scan")
async def run_scan(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    if not await collector_enabled(db):
        raise ApiError(409, "COLLECTOR_DISABLED", "Collector đang bị tắt (kill switch)")
    job_id = start_scan_job()
    response.status_code = 202
    return ok({"job_id": job_id, "kind": "scan", "status": "running"}, request)


@router.post("/run-deep")
async def run_deep(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    if not await collector_enabled(db):
        raise ApiError(409, "COLLECTOR_DISABLED", "Collector đang bị tắt (kill switch)")
    job_id = start_deep_job()
    response.status_code = 202
    return ok({"job_id": job_id, "kind": "deep", "status": "running"}, request)


@router.get("/jobs/{job_id}")
async def job_status(
    job_id: str,
    request: Request,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise ApiError(404, "JOB_NOT_FOUND", "Không tìm thấy job")
    return ok(job, request)


@router.post("/kill-switch")
async def kill_switch(
    request: Request,
    body: KillSwitchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    row = await set_setting(db, KILL_SWITCH_KEY, not body.active)
    return ok(
        {"key": KILL_SWITCH_KEY, "kill_switch": body.active, "enabled": not body.active,
         "version": row.version},
        request,
    )
