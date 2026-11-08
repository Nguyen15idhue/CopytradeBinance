from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.performance import PerformanceMetric
from app.models.position import Position
from app.models.risk_event import RiskEvent
from app.models.scoring_config import ScoringConfig
from app.models.snapshot import PortfolioSnapshot
from app.models.trade import Trade
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.transfer import Transfer
from app.models.user import User
from app.services.freshness import from_metrics as freshness_from_metrics

router = APIRouter(prefix="/traders", tags=["trader-detail"])

WINDOWS = ("7D", "30D", "90D", "180D")


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


async def _require_trader(db: AsyncSession, portfolio_id: str) -> Trader:
    trader = await db.get(Trader, portfolio_id)
    if trader is None:
        raise ApiError(404, "TRADER_NOT_FOUND", "Không tìm thấy trader")
    return trader


@router.get("/{portfolio_id}/performance")
async def performance(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    rows = (
        await db.execute(
            select(PerformanceMetric)
            .where(PerformanceMetric.lead_portfolio_id == portfolio_id)
            .order_by(PerformanceMetric.collected_at)
        )
    ).scalars().all()
    windows: dict[str, dict[str, Any]] = {}
    for row in rows:
        windows[row.time_range] = {
            "window": row.time_range,
            "roi": _float(row.roi),
            "pnl": _float(row.pnl),
            "mdd": _float(row.mdd),
            "copier_pnl": _float(row.copier_pnl),
            "win_rate": _float(row.win_rate),
            "win_orders": row.win_orders,
            "total_orders": row.total_orders,
            "sharpe": _float(row.sharpe),
            "collected_at": row.collected_at.isoformat(),
        }

    snapshot = (
        await db.execute(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.lead_portfolio_id == portfolio_id,
                PortfolioSnapshot.source.in_(("list", "demo")),
            )
            .order_by(PortfolioSnapshot.collected_at.desc())
            .limit(1)
        )
    ).scalars().first()
    chart = (snapshot.raw or {}).get("chartItems", []) if snapshot else []
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == portfolio_id)
        )
    ).scalars().first()
    return ok(
        {
            "windows": {window: windows.get(window) for window in WINDOWS},
            "chart": [
                {"date_time": item.get("dateTime"), "value": item.get("value")}
                for item in chart
                if isinstance(item, dict)
            ],
            "chart_note": (
                "ROI lũy kế từ chartItems của Binance; bị pha loãng bởi nạp/rút, "
                "không dùng để tính MDD tuyệt đối."
            ),
            "benchmark": None,
            "benchmark_note": "Chưa có nguồn klines; benchmark để null, không nội suy.",
            "freshness": freshness_from_metrics(metric.metrics if metric else None),
        },
        request,
    )


@router.get("/{portfolio_id}/positions")
async def positions(
    portfolio_id: str,
    request: Request,
    symbol: str | None = Query(default=None),
    side: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    statement = select(Position).where(Position.lead_portfolio_id == portfolio_id)
    if symbol:
        statement = statement.where(Position.symbol.ilike(f"%{symbol}%"))
    if side:
        statement = statement.where(Position.side.ilike(side))
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(desc(Position.closed_at).nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return ok(
        {
            "items": [
                {
                    "id": row.position_id,
                    "symbol": row.symbol,
                    "side": row.side,
                    "leverage": _float(row.leverage),
                    "isolated": row.isolated,
                    "opened_at": row.opened_at.isoformat() if row.opened_at else None,
                    "closed_at": row.closed_at.isoformat() if row.closed_at else None,
                    "closing_pnl": _float(row.closing_pnl),
                    "roi": _float(row.roi),
                    "status": row.status,
                }
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
        request,
    )


@router.get("/{portfolio_id}/trades")
async def trades(
    portfolio_id: str,
    request: Request,
    symbol: str | None = Query(default=None),
    side: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    statement = select(Trade).where(Trade.lead_portfolio_id == portfolio_id)
    if symbol:
        statement = statement.where(Trade.symbol.ilike(f"%{symbol}%"))
    if side:
        statement = statement.where(Trade.side.ilike(side))
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(desc(Trade.trade_time).nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return ok(
        {
            "items": [
                {
                    "hash": row.trade_hash[:12],
                    "time": row.trade_time.isoformat() if row.trade_time else None,
                    "symbol": row.symbol,
                    "side": row.side,
                    "price": _float(row.price),
                    "qty": _float(row.qty),
                    "notional": _float(row.quantity),
                    "fee": _float(row.fee),
                    "realized_profit": _float(row.realized_profit),
                    "position_side": row.position_side,
                }
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
        request,
    )


@router.get("/{portfolio_id}/transfers")
async def transfers(
    portfolio_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    statement = select(Transfer).where(Transfer.lead_portfolio_id == portfolio_id)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(desc(Transfer.transfer_time).nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return ok(
        {
            "items": [
                {
                    "time": row.transfer_time.isoformat() if row.transfer_time else None,
                    "coin": row.coin,
                    "amount": _float(row.amount),
                    "from": row.from_account,
                    "to": row.to_account,
                    "type": row.trans_type,
                }
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        },
        request,
    )


@router.get("/{portfolio_id}/risk")
async def risk(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == portfolio_id)
        )
    ).scalars().first()
    events = (
        await db.execute(
            select(RiskEvent)
            .where(RiskEvent.lead_portfolio_id == portfolio_id)
            .order_by(RiskEvent.severity)
        )
    ).scalars().all()
    return ok(
        {
            "risk_level": metric.risk_level if metric else None,
            "risk_score": (
                float(metric.risk_score)
                if metric and metric.risk_score is not None
                else None
            ),
            "veto_reasons": (metric.risk_veto or {}).get("reasons", []) if metric else [],
            "flags": (metric.metrics or {}).get("flags", []) if metric else [],
            "events": [
                {
                    "code": event.code,
                    "severity": event.severity,
                    "label": event.label,
                    "evidence": event.evidence,
                    "status": event.status,
                }
                for event in events
            ],
        },
        request,
    )


@router.get("/{portfolio_id}/score")
async def score(
    portfolio_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await _require_trader(db, portfolio_id)
    config = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    version = config.version if config else 1
    row = (
        await db.execute(
            select(TraderScore).where(
                TraderScore.lead_portfolio_id == portfolio_id,
                TraderScore.config_version == version,
            )
        )
    ).scalars().first()
    return ok(
        {
            "config_version": version,
            "score": _float(row.score) if row else None,
            "band": row.band if row else None,
            "confidence": _float(row.confidence) if row else None,
            "rankable": row.rankable if row else False,
            "hard_flags": row.hard_flags if row else [],
            "breakdown": row.breakdown if row else {},
        },
        request,
    )
