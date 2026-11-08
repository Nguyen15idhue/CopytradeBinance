"""Truy vấn screener trên trader_metrics + trader_scores."""

from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import Numeric, Select, and_, asc, cast, column, desc, exists, func, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring_config import ScoringConfig
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse
from app.services.freshness import from_metrics as freshness_from_metrics

TIER_ALIASES = {
    "qualified": "qualified_upper",
    "high": "high_upper",
    "watch": "watch",
    "excluded": "excluded",
}

WINDOW_KEYS = ("7D", "30D", "90D", "180D")
DEFAULT_WINDOW = "90D"

WINDOW_ATTRS: dict[str, dict[str, str]] = {
    "7D": {
        "roi": "roi_7d",
        "mdd": "mdd_7d",
        "sharpe": "sharpe_7d",
        "copier_pnl": "copier_pnl_7d",
        "win_rate": "win_rate_order_7d",
    },
    "30D": {
        "roi": "roi_30d",
        "mdd": "mdd_30d",
        "sharpe": "sharpe_30d",
        "copier_pnl": "copier_pnl_30d",
        "win_rate": "win_rate_order_30d",
    },
    "90D": {
        "roi": "roi_90d",
        "mdd": "mdd_90d",
        "sharpe": "sharpe_90d",
        "copier_pnl": "copier_pnl_90d",
        "win_rate": "win_rate_order_90d",
    },
    "180D": {
        "roi": "roi_180d",
        "mdd": "mdd_180d",
        "sharpe": "sharpe_180d",
        "copier_pnl": "copier_pnl_180d",
        "win_rate": "win_rate_order_180d",
    },
}

WINDOW_COLUMNS: dict[str, dict[str, Any]] = {
    window: {key: getattr(TraderMetric, attr) for key, attr in mapping.items()}
    for window, mapping in WINDOW_ATTRS.items()
}

BASE_SORT_COLUMNS = {
    "score": TraderScore.score,
    "confidence": TraderScore.confidence,
    "runtime_days": TraderMetric.runtime_days,
    "current_copiers": TraderMetric.current_copiers,
    "copy_aum": TraderMetric.copy_aum,
    "aum": TraderMetric.aum,
    "max_leverage": TraderMetric.max_leverage,
    "avg_leverage": TraderMetric.avg_leverage,
    "profit_factor": TraderMetric.profit_factor,
    "fee_drag_pct": TraderMetric.fee_drag_pct,
    "position_win_rate": TraderMetric.position_win_rate,
    "risk_score": TraderMetric.risk_score,
    "total_orders": TraderMetric.total_orders_90d,
    "pre_score": TraderUniverse.pre_score,
}


def sort_columns(window: str = DEFAULT_WINDOW) -> dict[str, Any]:
    columns = dict(BASE_SORT_COLUMNS)
    window_columns = WINDOW_COLUMNS.get(window, WINDOW_COLUMNS[DEFAULT_WINDOW])
    columns.update(window_columns)
    columns["roi_90d"] = TraderMetric.roi_90d
    columns["mdd_90d"] = TraderMetric.mdd_90d
    columns["sharpe_90d"] = TraderMetric.sharpe_90d
    return columns


SORT_COLUMNS = sort_columns(DEFAULT_WINDOW)

DEFAULT_SORT = "score"


@dataclass
class ScreenerFilters:
    q: str | None = None
    portfolio_type: str | None = None
    status: str | None = None
    potential_tier: list[str] = field(default_factory=list)
    include_excluded: bool = False
    window: str = DEFAULT_WINDOW
    min_pre_score: float | None = None
    min_roi: float | None = None
    max_roi: float | None = None
    max_mdd: float | None = None
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
    max_copiers: int | None = None
    min_copier_pnl: float | None = None
    max_copier_pnl: float | None = None
    min_copy_aum: float | None = None
    max_copy_aum: float | None = None
    min_aum: float | None = None
    max_aum: float | None = None
    max_leverage: float | None = None
    min_avg_leverage: float | None = None
    max_avg_leverage: float | None = None
    min_profit_factor: float | None = None
    max_profit_factor: float | None = None
    max_fee_drag_pct: float | None = None
    min_position_win_rate: float | None = None
    min_confidence: float | None = None
    max_risk_score: float | None = None
    min_copy_aum_ratio: float | None = None
    risk_level: list[str] = field(default_factory=list)
    has_sharpe: bool | None = None
    min_score: float | None = None
    max_min_copy_usd: float | None = None

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


def _window_key(window: str) -> str:
    return window if window in WINDOW_COLUMNS else DEFAULT_WINDOW


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
    if filters.min_roi is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["roi"] >= filters.min_roi
        )
    if filters.max_roi is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["roi"] <= filters.max_roi
        )
    if filters.max_mdd is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["mdd"] <= filters.max_mdd
        )
    if filters.min_roi_90d is not None:
        statement = statement.where(TraderMetric.roi_90d >= filters.min_roi_90d)
    if filters.max_roi_90d is not None:
        statement = statement.where(TraderMetric.roi_90d <= filters.max_roi_90d)
    if filters.max_mdd_90d is not None:
        statement = statement.where(TraderMetric.mdd_90d <= filters.max_mdd_90d)
    if filters.min_sharpe is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["sharpe"] >= filters.min_sharpe
        )
    if filters.max_sharpe is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["sharpe"] <= filters.max_sharpe
        )
    if filters.min_win_rate is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["win_rate"] >= filters.min_win_rate
        )
    if filters.max_win_rate is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["win_rate"] <= filters.max_win_rate
        )
    if filters.min_runtime_days is not None:
        statement = statement.where(TraderMetric.runtime_days >= filters.min_runtime_days)
    if filters.min_total_orders is not None:
        statement = statement.where(
            TraderMetric.total_orders_90d >= filters.min_total_orders
        )
    if filters.min_copiers is not None:
        statement = statement.where(TraderMetric.current_copiers >= filters.min_copiers)
    if filters.max_copiers is not None:
        statement = statement.where(TraderMetric.current_copiers <= filters.max_copiers)
    if filters.min_copier_pnl is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["copier_pnl"] >= filters.min_copier_pnl
        )
    if filters.max_copier_pnl is not None:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["copier_pnl"] <= filters.max_copier_pnl
        )
    if filters.min_copy_aum is not None:
        statement = statement.where(TraderMetric.copy_aum >= filters.min_copy_aum)
    if filters.max_copy_aum is not None:
        statement = statement.where(TraderMetric.copy_aum <= filters.max_copy_aum)
    if filters.min_aum is not None:
        statement = statement.where(TraderMetric.aum >= filters.min_aum)
    if filters.max_aum is not None:
        statement = statement.where(TraderMetric.aum <= filters.max_aum)
    if filters.max_leverage is not None:
        statement = statement.where(TraderMetric.max_leverage <= filters.max_leverage)
    if filters.min_avg_leverage is not None:
        statement = statement.where(TraderMetric.avg_leverage >= filters.min_avg_leverage)
    if filters.max_avg_leverage is not None:
        statement = statement.where(TraderMetric.avg_leverage <= filters.max_avg_leverage)
    if filters.min_profit_factor is not None:
        statement = statement.where(TraderMetric.profit_factor >= filters.min_profit_factor)
    if filters.max_profit_factor is not None:
        statement = statement.where(TraderMetric.profit_factor <= filters.max_profit_factor)
    if filters.max_fee_drag_pct is not None:
        statement = statement.where(TraderMetric.fee_drag_pct <= filters.max_fee_drag_pct)
    if filters.min_position_win_rate is not None:
        statement = statement.where(
            TraderMetric.position_win_rate >= filters.min_position_win_rate
        )
    if filters.min_confidence is not None:
        statement = statement.where(TraderScore.confidence >= filters.min_confidence)
    if filters.max_risk_score is not None:
        statement = statement.where(TraderMetric.risk_score <= filters.max_risk_score)
    if filters.min_copy_aum_ratio is not None:
        ratio = cast(
            TraderMetric.metrics["derived"]["copy_aum_ratio"].astext, Numeric(12, 4)
        )
        statement = statement.where(ratio >= filters.min_copy_aum_ratio)
    if filters.risk_level:
        statement = statement.where(TraderMetric.risk_level.in_(filters.risk_level))
    if filters.has_sharpe is True:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["sharpe"].is_not(None)
        )
    if filters.has_sharpe is False:
        statement = statement.where(
            WINDOW_COLUMNS[_window_key(filters.window)]["sharpe"].is_(None)
        )
    if filters.min_score is not None:
        statement = statement.where(TraderScore.score >= filters.min_score)
    if filters.max_min_copy_usd is not None:
        view = table(
            "agent_trader_copy_constraints",
            column("lead_portfolio_id"),
            column("fixed_radio_min_copy_usd"),
            column("fixed_amount_min_copy_usd"),
        )
        cheapest = func.coalesce(
            func.least(
                func.coalesce(view.c.fixed_radio_min_copy_usd, 1e12),
                func.coalesce(view.c.fixed_amount_min_copy_usd, 1e12),
            ),
            1e12,
        )
        statement = statement.where(
            exists(
                select(1)
                .select_from(view)
                .where(
                    view.c.lead_portfolio_id == TraderUniverse.lead_portfolio_id,
                    cheapest <= float(filters.max_min_copy_usd),
                )
            )
        )
    return statement


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _window_payload(metric: TraderMetric | None, window: str) -> dict[str, Any]:
    if metric is None:
        return {}
    mapping = WINDOW_ATTRS.get(window, {})
    return {key: _float(getattr(metric, attr, None)) for key, attr in mapping.items()}


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
        "avg_leverage": _float(metric.avg_leverage) if metric else None,
        "position_win_rate": _float(metric.position_win_rate) if metric else None,
        "risk_score": _float(metric.risk_score) if metric else None,
        "windows": {
            "7D": _window_payload(metric, "7D"),
            "30D": _window_payload(metric, "30D"),
            "90D": _window_payload(metric, "90D"),
            "180D": _window_payload(metric, "180D"),
        } if metric else {},
        "low_sample": metric.low_sample if metric else False,
        "filter_reasons": universe.filter_reasons or [],
        "breakdown": (score.breakdown if score else None) or {},
        "computed_at": metric.computed_at.isoformat() if metric else None,
        "freshness": freshness_from_metrics(metrics) if metric else None,
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

    window = _window_key(filters.window)
    window_column = WINDOW_COLUMNS[window]["roi"]
    window_rows = await db.scalar(
        select(func.count()).select_from(TraderMetric).where(window_column.is_not(None))
    )
    window_missing = not bool(window_rows)

    column = sort_columns(window).get(sort_by, TraderScore.score)
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
        "sort_by": sort_by if sort_by in sort_columns(window) else DEFAULT_SORT,
        "sort_dir": sort_dir,
        "config_version": version,
        "window": window,
        "window_missing": window_missing,
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
