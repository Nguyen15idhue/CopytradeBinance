from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.performance import PerformanceMetric
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.universe import TraderUniverse
from app.models.user import User
from app.services.freshness import from_metrics as freshness_from_metrics

router = APIRouter(prefix="/traders", tags=["traders"])


def _float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    number = _num(value)
    return int(number) if number is not None else None


def _metric(
    key: str,
    label: str,
    value: Any,
    unit: str,
    source: str,
    window: str | None = "90D",
    note: str | None = None,
) -> dict:
    return {
        "key": key,
        "label": label,
        "value": value,
        "unit": unit,
        "source": source,
        "window": window,
        "note": note,
    }


def _confidence(values: list[Any]) -> float:
    present = sum(1 for value in values if value is not None)
    return round(present / len(values), 2) if values else 0.0


@router.get("/{portfolio_id}")
async def get_trader(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    trader = await db.get(Trader, portfolio_id)
    if trader is None:
        raise ApiError(404, "TRADER_NOT_FOUND", "Không tìm thấy trader")

    universe = await db.get(TraderUniverse, portfolio_id)

    snapshot_result = await db.execute(
        select(PortfolioSnapshot)
        .where(
            PortfolioSnapshot.lead_portfolio_id == portfolio_id,
            PortfolioSnapshot.source.in_(("demo", "detail", "list")),
        )
        .order_by(
            case(
                (PortfolioSnapshot.source == "demo", 0),
                (PortfolioSnapshot.source == "detail", 1),
                else_=2,
            ),
            desc(PortfolioSnapshot.collected_at),
        )
        .limit(1)
    )
    snapshot = snapshot_result.scalar_one_or_none()
    raw = snapshot.raw if snapshot else {}

    metric_result = await db.execute(
        select(PerformanceMetric)
        .where(
            PerformanceMetric.lead_portfolio_id == portfolio_id,
            PerformanceMetric.time_range == "90D",
        )
        .order_by(desc(PerformanceMetric.collected_at))
        .limit(1)
    )
    metric = metric_result.scalar_one_or_none()
    trader_metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == portfolio_id)
        )
    ).scalars().first()
    freshness = freshness_from_metrics(
        trader_metric.metrics if trader_metric else None
    )

    tier = universe.potential_tier if universe else "unknown"
    reasons = universe.filter_reasons if universe else ["not_in_universe"]
    runtime_days = raw.get("runtimeDays")
    if runtime_days is None and trader.start_time is not None:
        delta = datetime.now(UTC) - trader.start_time
        runtime_days = round(delta.total_seconds() / 86_400, 2)
    aum = _num(raw.get("aum") or raw.get("aumAmount"))
    copy_aum = _num(raw.get("copyAum"))
    current_copiers = _int(raw.get("currentCopyCount"))
    max_copiers = _int(raw.get("maxCopyCount"))
    leverage = _num(raw.get("leverage") or raw.get("maxLeverage"))

    mdd = _float(metric.mdd) if metric else None
    sharpe = _float(metric.sharpe) if metric else None
    win_rate = _float(metric.win_rate) if metric else None
    copier_pnl = _float(metric.copier_pnl) if metric else None
    roi = _float(metric.roi) if metric else None
    pnl = _float(metric.pnl) if metric else None
    profit_factor = None
    avg_holding = None

    metrics = [
        _metric("roi_90d", "ROI 90D", roi, "%", "published"),
        _metric("mdd_90d", "MDD 90D", mdd, "%", "published", note="Dùng MDD do Binance công bố"),
        _metric("sharpe", "Sharpe", sharpe, "", "published", note="N/A nếu null"),
        _metric("win_rate_order", "WinRate (order)", win_rate, "%", "published"),
        _metric("profit_factor", "Profit Factor", profit_factor, "", "derived", window=None),
        _metric("max_leverage", "Max Leverage", leverage, "x", "derived", window=None),
        _metric("avg_holding", "Avg Holding", avg_holding, "giờ", "derived", window=None),
        _metric("copier_pnl", "Copier PnL", copier_pnl, "USDT", "published"),
        _metric("copy_aum", "Copy AUM", copy_aum, "USDT", "detail", window=None),
        _metric("copiers", "Copiers", current_copiers, "người", "detail", window=None,
                note=f"Tối đa {max_copiers}" if max_copiers is not None else None),
    ]

    confidence = _confidence(
        [roi, mdd, sharpe, win_rate, copier_pnl, aum, copy_aum, current_copiers, leverage]
    )
    flags: list[str] = []
    if sharpe is None:
        flags.append("missing_sharpe")
    if mdd is None:
        flags.append("missing_mdd")
    if copy_aum == 0 and current_copiers == 0:
        flags.append("no_copiers")
    if metric and metric.total_orders is not None and metric.total_orders < 20:
        flags.append("low_sample")
    if tier == "excluded":
        flags.append("excluded")
    flags.append("derived_unavailable")

    collected_at = snapshot.collected_at if snapshot else None
    return ok(
        {
            "trader": {
                "id": trader.lead_portfolio_id,
                "nickname": trader.nickname,
                "portfolio_type": trader.portfolio_type,
                "status": trader.status,
                "description": trader.description,
                "runtime_days": runtime_days,
                "last_trade_time": trader.last_trade_time.isoformat()
                if trader.last_trade_time
                else None,
            },
            "tier": tier,
            "reasons": reasons,
            "pre_score": _float(universe.pre_score) if universe else None,
            "metrics": metrics,
            "profile": {
                "aum": aum,
                "copy_aum": copy_aum,
                "current_copy_count": current_copiers,
                "max_copy_count": max_copiers,
                "leverage": leverage,
                "win_orders": metric.win_orders if metric else None,
                "total_orders": metric.total_orders if metric else None,
                "pnl": pnl,
            },
            "confidence": confidence,
            "flags": flags,
            "provenance": {
                "source": snapshot.source if snapshot else None,
                "collected_at": collected_at.isoformat() if collected_at else None,
                "endpoint": "demo",
                "window": "90D",
                "published": metric is not None,
            },
            "freshness": freshness,
            "disclaimer": (
                "Công cụ phân tích dữ liệu công khai, không phải tư vấn đầu tư. "
                "Copy trading có rủi ro mất toàn bộ vốn."
            ),
            "generated_at": datetime.now(UTC).isoformat(),
        },
        request,
    )
