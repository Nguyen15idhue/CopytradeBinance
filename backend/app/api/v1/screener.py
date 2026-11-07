import csv
import io
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.models.user import User
from app.services.screener import (
    ScreenerFilters,
    funnel_summary,
    list_traders,
)

router = APIRouter(prefix="/traders", tags=["screener"])

EXPORT_COLUMNS = [
    ("id", "Mã trader"),
    ("nickname", "Biệt danh"),
    ("potential_tier", "Nhóm"),
    ("score", "Điểm"),
    ("band", "Mức điểm"),
    ("confidence", "Độ tin cậy"),
    ("roi_90d", "ROI 90D"),
    ("mdd_90d", "MDD 90D"),
    ("sharpe", "Sharpe"),
    ("win_rate_order_90d", "WinRate"),
    ("total_orders_90d", "Số lệnh"),
    ("runtime_days", "Số ngày hoạt động"),
    ("current_copiers", "Số copier"),
    ("copy_aum", "Copy AUM"),
    ("max_leverage", "Đòn bẩy tối đa"),
    ("risk_level", "Rủi ro"),
]


def _filters(**values: Any) -> ScreenerFilters:
    values["potential_tier"] = values.get("potential_tier") or []
    values["risk_level"] = values.get("risk_level") or []
    values.setdefault("include_excluded", False)
    return ScreenerFilters(**values)


@router.get("")
async def screener(
    request: Request,
    q: str | None = Query(default=None),
    portfolio_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    potential_tier: list[str] | None = Query(default=None),
    include_excluded: bool = Query(default=False),
    min_pre_score: float | None = Query(default=None),
    min_roi_90d: float | None = Query(default=None),
    max_roi_90d: float | None = Query(default=None),
    max_mdd_90d: float | None = Query(default=None),
    min_sharpe: float | None = Query(default=None),
    max_sharpe: float | None = Query(default=None),
    min_win_rate: float | None = Query(default=None),
    max_win_rate: float | None = Query(default=None),
    min_runtime_days: float | None = Query(default=None),
    min_total_orders: int | None = Query(default=None),
    min_copiers: int | None = Query(default=None),
    max_copiers: int | None = Query(default=None),
    min_copier_pnl: float | None = Query(default=None),
    max_copier_pnl: float | None = Query(default=None),
    min_copy_aum: float | None = Query(default=None),
    max_copy_aum: float | None = Query(default=None),
    min_aum: float | None = Query(default=None),
    max_aum: float | None = Query(default=None),
    max_leverage: float | None = Query(default=None),
    min_avg_leverage: float | None = Query(default=None),
    max_avg_leverage: float | None = Query(default=None),
    min_profit_factor: float | None = Query(default=None),
    max_profit_factor: float | None = Query(default=None),
    max_fee_drag_pct: float | None = Query(default=None),
    min_position_win_rate: float | None = Query(default=None),
    min_confidence: float | None = Query(default=None),
    max_risk_score: float | None = Query(default=None),
    min_copy_aum_ratio: float | None = Query(default=None),
    risk_level: list[str] | None = Query(default=None),
    has_sharpe: bool | None = Query(default=None),
    min_score: float | None = Query(default=None),
    max_min_copy_usd: float | None = Query(default=None),
    window: str = Query(default="90D"),
    min_roi: float | None = Query(default=None),
    max_roi: float | None = Query(default=None),
    max_mdd: float | None = Query(default=None),
    sort_by: str = Query(default="score"),
    sort_dir: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    filters = _filters(
        q=q,
        portfolio_type=portfolio_type,
        status=status,
        potential_tier=potential_tier,
        include_excluded=include_excluded,
        min_pre_score=min_pre_score,
        min_roi=min_roi,
        max_roi=max_roi,
        max_mdd=max_mdd,
        min_roi_90d=min_roi_90d,
        max_roi_90d=max_roi_90d,
        max_mdd_90d=max_mdd_90d,
        min_sharpe=min_sharpe,
        max_sharpe=max_sharpe,
        min_win_rate=min_win_rate,
        max_win_rate=max_win_rate,
        min_runtime_days=min_runtime_days,
        min_total_orders=min_total_orders,
        min_copiers=min_copiers,
        max_copiers=max_copiers,
        min_copier_pnl=min_copier_pnl,
        max_copier_pnl=max_copier_pnl,
        min_copy_aum=min_copy_aum,
        max_copy_aum=max_copy_aum,
        min_aum=min_aum,
        max_aum=max_aum,
        max_leverage=max_leverage,
        min_avg_leverage=min_avg_leverage,
        max_avg_leverage=max_avg_leverage,
        min_profit_factor=min_profit_factor,
        max_profit_factor=max_profit_factor,
        max_fee_drag_pct=max_fee_drag_pct,
        min_position_win_rate=min_position_win_rate,
        min_confidence=min_confidence,
        max_risk_score=max_risk_score,
        min_copy_aum_ratio=min_copy_aum_ratio,
        risk_level=risk_level,
        has_sharpe=has_sharpe,
        min_score=min_score,
        max_min_copy_usd=max_min_copy_usd,
        window=window,
    )
    result = await list_traders(
        db, filters, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir
    )
    return ok(result, request)


@router.get("/funnel-summary")
async def funnel(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return ok(await funnel_summary(db), request)


@router.get("/export.csv")
async def export_csv(
    request: Request,
    q: str | None = Query(default=None),
    portfolio_type: str | None = Query(default=None),
    potential_tier: list[str] | None = Query(default=None),
    include_excluded: bool = Query(default=False),
    max_mdd_90d: float | None = Query(default=None),
    min_roi_90d: float | None = Query(default=None),
    min_sharpe: float | None = Query(default=None),
    min_win_rate: float | None = Query(default=None),
    min_runtime_days: float | None = Query(default=None),
    min_total_orders: int | None = Query(default=None),
    max_leverage: float | None = Query(default=None),
    risk_level: list[str] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    filters = ScreenerFilters(
        q=q,
        portfolio_type=portfolio_type,
        potential_tier=potential_tier or [],
        include_excluded=include_excluded,
        max_mdd_90d=max_mdd_90d,
        min_roi_90d=min_roi_90d,
        min_sharpe=min_sharpe,
        min_win_rate=min_win_rate,
        min_runtime_days=min_runtime_days,
        min_total_orders=min_total_orders,
        max_leverage=max_leverage,
        risk_level=risk_level or [],
    )
    data = await list_traders(db, filters, page=1, page_size=100)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([label for _key, label in EXPORT_COLUMNS])
    for item in data["items"]:
        writer.writerow([item.get(key) for key, _label in EXPORT_COLUMNS])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=traders.csv"},
    )
