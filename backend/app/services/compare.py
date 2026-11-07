"""So sánh 2–4 trader + correlation ước tính từ chartItems."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring_config import ScoringConfig
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse

DISCLAIMER = (
    "Correlation estimated từ ROI lũy kế chartItems (sai phân theo ngày), "
    "bị pha loãng bởi nạp/rút; không dùng cho position sizing."
)


def _series(chart: list[dict[str, Any]]) -> dict[int, float]:
    return {
        int(item["dateTime"]): float(item["value"])
        for item in chart
        if isinstance(item, dict) and item.get("dateTime") and item.get("value") is not None
    }


def _returns(series: dict[int, float]) -> dict[int, float]:
    dates = sorted(series)
    return {
        dates[index]: series[dates[index]] - series[dates[index - 1]]
        for index in range(1, len(dates))
    }


def _pearson(a: dict[int, float], b: dict[int, float]) -> float | None:
    common = sorted(set(a) & set(b))
    if len(common) < 30:
        return None
    xs = [a[key] for key in common]
    ys = [b[key] for key in common]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return None
    return round(cov / (var_x**0.5 * var_y**0.5), 4)


def correlation_matrix(charts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ids = list(charts)
    returns = {pid: _returns(_series(charts[pid])) for pid in ids}
    matrix: list[list[float | None]] = []
    sample_days = 0
    for left in ids:
        row: list[float | None] = []
        for right in ids:
            if left == right:
                row.append(1.0)
            else:
                value = _pearson(returns[left], returns[right])
                row.append(value)
        matrix.append(row)
    common_sets = [set(returns[pid]) for pid in ids]
    if common_sets:
        sample_days = len(set.intersection(*common_sets))
    return {
        "ids": ids,
        "matrix": matrix,
        "sample_days": sample_days,
        "disclaimer": DISCLAIMER,
    }


async def build_compare(db: AsyncSession, ids: list[str]) -> dict[str, Any]:
    config = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    version = config.version if config else 1

    rows = (
        await db.execute(
            select(TraderMetric, TraderScore, TraderUniverse, Trader.nickname)
            .join(
                TraderUniverse,
                TraderUniverse.lead_portfolio_id == TraderMetric.lead_portfolio_id,
            )
            .join(Trader, Trader.lead_portfolio_id == TraderMetric.lead_portfolio_id)
            .outerjoin(
                TraderScore,
                (TraderScore.lead_portfolio_id == TraderMetric.lead_portfolio_id)
                & (TraderScore.config_version == version),
            )
            .where(TraderMetric.lead_portfolio_id.in_(ids))
        )
    ).all()

    charts: dict[str, list[dict[str, Any]]] = {}
    for pid in ids:
        snapshot = (
            await db.execute(
                select(PortfolioSnapshot)
                .where(
                    PortfolioSnapshot.lead_portfolio_id == pid,
                    PortfolioSnapshot.source.in_(("list", "demo")),
                )
                .order_by(PortfolioSnapshot.collected_at.desc())
                .limit(1)
            )
        ).scalars().first()
        charts[pid] = (snapshot.raw or {}).get("chartItems", []) if snapshot else []

    items = []
    for metric, score, universe, nickname in rows:
        metrics = metric.metrics or {}
        published = (metrics.get("published") or {}).get("90D", {})
        derived = metrics.get("derived") or {}
        items.append(
            {
                "id": metric.lead_portfolio_id,
                "nickname": nickname,
                "tier": universe.potential_tier,
                "score": float(score.score) if score and score.score is not None else None,
                "band": score.band if score else None,
                "confidence": float(score.confidence)
                if score and score.confidence is not None
                else None,
                "risk_level": metric.risk_level,
                "roi_90d": float(metric.roi_90d) if metric.roi_90d is not None else None,
                "mdd_90d": float(metric.mdd_90d) if metric.mdd_90d is not None else None,
                "sharpe": float(metric.sharpe_90d) if metric.sharpe_90d is not None else None,
                "win_rate_order": float(metric.win_rate_order_90d)
                if metric.win_rate_order_90d is not None
                else None,
                "max_leverage": float(metric.max_leverage)
                if metric.max_leverage is not None
                else None,
                "profit_factor": float(metric.profit_factor)
                if metric.profit_factor is not None
                else None,
                "runtime_days": float(metric.runtime_days)
                if metric.runtime_days is not None
                else None,
                "copier_pnl_90d": float(metric.copier_pnl_90d)
                if metric.copier_pnl_90d is not None
                else None,
                "copy_aum": float(metric.copy_aum) if metric.copy_aum is not None else None,
                "windows": {
                    window: {
                        "roi": (metrics.get("published") or {}).get(window, {}).get("roi"),
                        "mdd": (metrics.get("published") or {}).get(window, {}).get("mdd"),
                    }
                    for window in ("7D", "30D", "90D", "180D")
                },
                "pnl_90d": published.get("pnl"),
                "top_symbol": derived.get("top_symbol"),
            }
        )

    return {
        "items": items,
        "series": {
            pid: [
                {"date_time": item.get("dateTime"), "value": item.get("value")}
                for item in charts.get(pid, [])
                if isinstance(item, dict)
            ]
            for pid in ids
        },
        "correlation": correlation_matrix({pid: charts.get(pid, []) for pid in ids}),
        "missing": [pid for pid in ids if pid not in {item["id"] for item in items}],
    }


async def count_traders(db: AsyncSession) -> int:
    return int(await db.scalar(select(func.count()).select_from(TraderMetric)) or 0)
