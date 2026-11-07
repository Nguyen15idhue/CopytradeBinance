from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.models.user import User
from app.services.universe import latest_scan_log, recompute_universe

router = APIRouter(prefix="/universe", tags=["universe"])

TIER_ALIASES = {"qualified": "qualified_upper", "high": "high_upper"}


def _normalize_tier(value: str | None) -> str | None:
    if value is None:
        return None
    return TIER_ALIASES.get(value, value)


@router.get("/summary")
async def summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    rows = (
        await db.execute(
            select(TraderUniverse.potential_tier, func.count()).group_by(
                TraderUniverse.potential_tier
            )
        )
    ).all()
    counts = {tier: count for tier, count in rows}
    watch_total = sum(counts.get(name, 0) for name in ("watch", "qualified_upper", "high_upper"))
    log = await latest_scan_log(db)
    return ok(
        {
            "counts": counts,
            "total": sum(counts.values()),
            "watch_total": watch_total,
            "qualified_total": counts.get("qualified_upper", 0) + counts.get("high_upper", 0),
            "high_total": counts.get("high_upper", 0),
            "cohort": "all",
            "last_scan": {
                "status": log.status if log else None,
                "started_at": log.started_at.isoformat() if log else None,
                "finished_at": log.finished_at.isoformat() if log and log.finished_at else None,
                "pages": log.pages if log else 0,
                "items_ok": log.items_ok if log else 0,
                "duration_seconds": (log.detail or {}).get("duration_seconds") if log else None,
            },
            "generated_at": datetime.now(UTC).isoformat(),
        },
        request,
    )


@router.get("/traders")
async def list_universe(
    request: Request,
    tier: str | None = Query(default=None),
    reason: str | None = Query(default=None),
    min_pre_score: float | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    statement = select(TraderUniverse, Trader).join(
        Trader, Trader.lead_portfolio_id == TraderUniverse.lead_portfolio_id
    )
    normalized = _normalize_tier(tier)
    if normalized:
        statement = statement.where(TraderUniverse.potential_tier == normalized)
    if reason:
        statement = statement.where(TraderUniverse.filter_reasons.contains([reason]))
    if min_pre_score is not None:
        statement = statement.where(TraderUniverse.pre_score >= min_pre_score)
    if q:
        statement = statement.where(Trader.nickname.ilike(f"%{q}%"))

    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(
                TraderUniverse.pre_score.desc().nullslast(),
                TraderUniverse.lead_portfolio_id,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    items = []
    for universe_row, trader in rows:
        items.append(
            {
                "id": universe_row.lead_portfolio_id,
                "nickname": trader.nickname,
                "portfolio_type": trader.portfolio_type,
                "potential_tier": universe_row.potential_tier,
                "pre_score": float(universe_row.pre_score)
                if universe_row.pre_score is not None
                else None,
                "filter_reasons": universe_row.filter_reasons or [],
                "deep_fetch_status": universe_row.deep_fetch_status,
            }
        )
    return ok(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
        request,
    )


@router.post("/recompute")
async def recompute(
    request: Request,
    aum_min: int | None = Query(default=None, ge=1000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    result = await recompute_universe(db, aum_min=aum_min)
    return ok(result, request)
