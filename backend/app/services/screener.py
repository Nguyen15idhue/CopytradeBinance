"""Truy vấn screener trên trader_metrics + trader_scores."""

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import Select, and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring_config import ScoringConfig
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse

TIER_ALIASES = {
    "qualified": "qualified_upper",
    "high": "high_upper",
    "watch": "watch",
    "excluded": "excluded",
}

SORT_COLUMNS = {
    "score": TraderScore.score,
    "confidence": TraderScore.confidence,
    "roi_90d": TraderMetric.roi_90d,
    "mdd_90d": TraderMetric.mdd_90d,
    "sharpe": TraderMetric.sharpe_90d,
    "win_rate": TraderMetric.win_rate_order_90d,
    "runtime_days": TraderMetric.runtime_days,
    "current_copiers": TraderMetric.current_copiers,
    "copy_aum": TraderMetric.copy_aum,
    "max_leverage": TraderMetric.max_leverage,
    "pre_score": TraderUniverse.pre_score,
    "total_orders": TraderMetric.total_orders_90d,
}

DEFAULT_SORT = "score"


@dataclass
class ScreenerFilters:
    q: str | None = None
    portfolio_type: str | None = None
    status: str | None = None
    potential_tier: list[str] = field(default_factory=list)
    include_excluded: bool = False
    min_pre_score: float | None = None
    min_roi_90d: float | None = None
    max_roi_90d: float | None = None
    max_mdd_90d: float | None = None
    min_sharpe: float | None = None
    max_sharpe: float | None = None
    min_win_rate: float | None = None
    max_win_rate: float | None = None
    min_runtime_days: float | None = None
    min_total_orders: int | None = None
    min_copiers: int | None = None
    min_copy_aum: float | None = None
    max_leverage: float | None = None
    risk_level: list[str] = field(default_factory=list)
    has_sharpe: bool | None = None

    def normalized_tiers(self) -> list[str]:
        return [TIER_ALIASES.get(tier, tier) for tier in self.potential_tier]

    def as_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if value not in (None, [], "")
        }


def base_statement(config_version: int) -> Select:
    return (
        select(
            TraderUniverse,
            Trader.nickname,
            Trader.portfolio_type,
            Trader.status,
            TraderMetric,
            TraderScore,
        )
        .join(Trader, Trader.lead_portfolio_id == TraderUniverse.lead_portfolio_id)
        .outerjoin(
            TraderMetric, TraderMetric.lead_portfolio_id == TraderUniverse.lead_portfolio_id
        )
        .outerjoin(
            TraderScore,
            and_(
                TraderScore.lead_portfolio_id == TraderUniverse.lead_portfolio_id,
                TraderScore.config_version == config_version,
            ),
        )
    )


def apply_filters(statement: Select, filters: ScreenerFilters) -> Select:
    tiers = filters.normalized_tiers()
    if tiers:
        statement = statement.where(TraderUniverse.potential_tier.in_(tiers))
    elif not filters.include_excluded:
        statement = statement.where(TraderUniverse.potential_tier != "excluded")
    if filters.q:
        statement = statement.where(Trader.nickname.ilike(f"%{filters.q}%"))
    if filters.portfolio_type:
        statement = statement.where(Trader.portfolio_type == filters.portfolio_type.upper())
    if filters.status:
        statement = statement.where(Trader.status == filters.status.upper())
    if filters.min_pre_score is not None:
        statement = statement.where(TraderUniverse.pre_score >= filters.min_pre_score)
    if filters.min_roi_90d is not None:
        statement = statement.where(TraderMetric.roi_90d >= filters.min_roi_90d)
    if filters.max_roi_90d is not None:
        statement = statement.where(TraderMetric.roi_90d <= filters.max_roi_90d)
    if filters.max_mdd_90d is not None:
        statement = statement.where(TraderMetric.mdd_90d <= filters.max_mdd_90d)
    if filters.min_sharpe is not None:
        statement = statement.where(TraderMetric.sharpe_90d >= filters.min_sharpe)
    if filters.max_sharpe is not None:
        statement = statement.where(TraderMetric.sharpe_90d <= filters.max_sharpe)
    if filters.min_win_rate is not None:
        statement = statement.where(TraderMetric.win_rate_order_90d >= filters.min_win_rate)
    if filters.max_win_rate is not None:
        statement = statement.where(TraderMetric.win_rate_order_90d <= filters.max_win_rate)
    if filters.min_runtime_days is not None:
        statement = statement.where(TraderMetric.runtime_days >= filters.min_runtime_days)
    if filters.min_total_orders is not None:
        statement = statement.where(
            TraderMetric.total_orders_90d >= filters.min_total_orders
        )
    if filters.min_copiers is not None:
        statement = statement.where(TraderMetric.current_copiers >= filters.min_copiers)
    if filters.min_copy_aum is not None:
        statement = statement.where(TraderMetric.copy_aum >= filters.min_copy_aum)
    if filters.max_leverage is not None:
        statement = statement.where(TraderMetric.max_leverage <= filters.max_leverage)
    if filters.risk_level:
        statement = statement.where(TraderMetric.risk_level.in_(filters.risk_level))
    if filters.has_sharpe is True:
        statement = statement.where(TraderMetric.sharpe_90d.is_not(None))
    if filters.has_sharpe is False:
        statement = statement.where(TraderMetric.sharpe_90d.is_(None))
    return statement


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def serialize_row(row) -> dict[str, Any]:
    universe, nickname, portfolio_type, status, metric, score = row
    metrics = (metric.metrics if metric else None) or {}
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    return {
        "id": universe.lead_portfolio_id,
        "nickname": nickname,
        "portfolio_type": portfolio_type,
        "status": status,
        "potential_tier": universe.potential_tier,
        "pre_score": _float(universe.pre_score),
        "score": _float(score.score) if score else None,
        "band": score.band if score else None,
        "confidence": _float(score.confidence) if score else None,
        "rankable": score.rankable if score else False,
        "hard_flags": (score.hard_flags if score else None) or [],
        "risk_level": metric.risk_level if metric else None,
        "roi_90d": _float(metric.roi_90d) if metric else None,
        "mdd_90d": _float(metric.mdd_90d) if metric else None,
        "sharpe": _float(metric.sharpe_90d) if metric else None,
        "win_rate_order_90d": _float(metric.win_rate_order_90d) if metric else None,
        "win_orders": published.get("win_orders"),
        "total_orders_90d": metric.total_orders_90d if metric else None,
        "runtime_days": _float(metric.runtime_days) if metric else None,
        "current_copiers": metric.current_copiers if metric else None,
        "copy_aum": _float(metric.copy_aum) if metric else None,
        "aum": _float(metric.aum) if metric else None,
        "max_leverage": _float(metric.max_leverage) if metric else None,
        "profit_factor": _float(metric.profit_factor) if metric else None,
        "fee_drag_pct": _float(metric.fee_drag_pct) if metric else None,
        "low_sample": metric.low_sample if metric else False,
        "filter_reasons": universe.filter_reasons or [],
        "breakdown": (score.breakdown if score else None) or {},
        "computed_at": metric.computed_at.isoformat() if metric else None,
        "top_symbol": derived.get("top_symbol"),
    }


async def active_config_version(db: AsyncSession) -> int:
    config = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    return config.version if config else 1


async def list_traders(
    db: AsyncSession,
    filters: ScreenerFilters,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = DEFAULT_SORT,
    sort_dir: Literal["asc", "desc"] = "desc",
) -> dict[str, Any]:
    version = await active_config_version(db)
    statement = apply_filters(base_statement(version), filters)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))

    column = SORT_COLUMNS.get(sort_by, TraderScore.score)
    ordering = asc(column) if sort_dir == "asc" else desc(column)
    rows = (
        await db.execute(
            statement.order_by(ordering.nulls_last(), TraderMetric.lead_portfolio_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    return {
        "items": [serialize_row(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
        "sort_by": sort_by if sort_by in SORT_COLUMNS else DEFAULT_SORT,
        "sort_dir": sort_dir,
        "config_version": version,
    }


async def funnel_summary(db: AsyncSession) -> dict[str, Any]:
    rows = (
        await db.execute(
            select(TraderUniverse.potential_tier, func.count()).group_by(
                TraderUniverse.potential_tier
            )
        )
    ).all()
    counts = {tier: count for tier, count in rows}
    total = sum(counts.values())
    return {
        "universe": total,
        "watch": counts.get("watch", 0),
        "qualified": counts.get("qualified_upper", 0),
        "high": counts.get("high_upper", 0),
        "excluded": counts.get("excluded", 0),
    }
