
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.user import User
from app.services.settings_service import (
    SettingsUpdate,
    get_settings_snapshot,
    list_versions,
    preview_impact,
    rollback,
    update_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def read_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return ok(await get_settings_snapshot(db), request)


@router.put("")
async def write_settings(
    request: Request,
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    return ok(await update_settings(db, body, user.id), request)


@router.post("/preview")
async def preview(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    weights = body.get("weights") or {}
    if not isinstance(weights, dict) or not weights:
        raise ApiError(422, "INVALID_WEIGHTS", "Thiếu weights để preview")
    return ok(await preview_impact(db, weights, body.get("version")), request)


@router.get("/versions")
async def versions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = await list_versions(db)
    return ok(
        [
            {
                "version": row.version,
                "is_active": row.is_active,
                "weights": row.weights,
                "hard_filters": row.hard_filters,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        request,
    )


@router.post("/rollback/{version}")
async def rollback_version(
    version: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    return ok(await rollback(db, version, user.id), request)
