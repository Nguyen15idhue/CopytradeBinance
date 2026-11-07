"""Seed scoring config và tính trader_scores theo version."""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring_config import ScoringConfig
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse
from app.services import scoring as sc

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "weights": sc.GROUP_WEIGHTS,
    "normalization": {
        "method": "percentile_rank",
        "winsorize": [sc.WINSOR_LOW, sc.WINSOR_HIGH],
        "missing": "renormalize",
        "cohort": "portfolio_type+window",
    },
    "hard_filters": {
        "hf01": "status != ACTIVE",
        "hf02": "tier = excluded",
        "hf03": "runtime_days < 30",
        "hf04": {"watch": 20, "qualified": 50, "high": 100},
        "hf05": "freshness > 150m",
        "hf06": "confidence < 0.5",
    },
}


async def ensure_active_config(db: AsyncSession) -> ScoringConfig:
    active = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    if active is not None:
        return active
    config = ScoringConfig(version=1, is_active=True, **DEFAULT_CONFIG)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


def _components(metrics: dict[str, Any]) -> dict[str, float | None]:
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    profile = metrics.get("profile") or {}
    pnl = published.get("pnl")
    aum = profile.get("aum")
    orders = published.get("total_orders")
    return {
        "mdd": published.get("mdd"),
        "calmar": derived.get("calmar"),
        "max_leverage": derived.get("max_leverage"),
        "worst_position_roi": derived.get("worst_position_roi"),
        "positive_days_pct": derived.get("positive_days_pct"),
        "roi_stability": derived.get("roi_stability"),
        "roi_90d": published.get("roi"),
        "excess_return": metrics.get("excess_return"),
        "pnl_scale": sc.pnl_scale(pnl),
        "profit_factor": derived.get("profit_factor"),
        "payoff_ratio": derived.get("payoff_ratio"),
        "win_rate_order_90d": published.get("win_rate_order"),
        "copier_pnl_90d": published.get("copier_pnl"),
        "copy_aum_ratio": derived.get("copy_aum_ratio"),
        "current_copiers": profile.get("current_copiers"),
        "pnl_per_aum": sc.pnl_per_aum(pnl, aum),
        "aum": aum,
        "confidence": (metrics.get("confidence") or {}).get("value"),
        "sample_size": min(orders, 500) if orders is not None else None,
    }


async def build_scores(db: AsyncSession) -> dict[str, Any]:
    started = time.monotonic()
    config = await ensure_active_config(db)
    rows = (
        await db.execute(
            select(TraderMetric, TraderUniverse.potential_tier)
            .join(
                TraderUniverse,
                TraderUniverse.lead_portfolio_id == TraderMetric.lead_portfolio_id,
            )
            .order_by(TraderMetric.lead_portfolio_id)
        )
    ).all()

    prepared: list[dict[str, Any]] = []
    for metric, tier in rows:
        prepared.append(
            {
                "id": metric.lead_portfolio_id,
                "tier": tier,
                "metrics": metric.metrics,
                "components": _components(metric.metrics),
            }
        )

    scored = sc.compute_scores(prepared)
    score_rows: list[dict[str, Any]] = []
    for source, result in zip(prepared, scored, strict=True):
        metrics = source["metrics"]
        confidence = (metrics.get("confidence") or {}).get("value")
        flags = sc.hard_flags(
            status=(metrics.get("profile") or {}).get("status"),
            tier=source["tier"],
            runtime_days=metrics.get("runtime_days"),
            total_orders=(metrics.get("published") or {}).get("90D", {}).get("total_orders"),
            freshness_minutes=metrics.get("freshness_minutes"),
            confidence=confidence,
        )
        rankable = result["score"] is not None and not flags
        score_rows.append(
            {
                "lead_portfolio_id": source["id"],
                "config_version": config.version,
                "score": result["score"],
                "band": result["band"],
                "confidence": confidence,
                "rankable": rankable,
                "hard_flags": flags,
                "breakdown": {
                    "components": result["components"],
                    "missing": result["missing"],
                    "score": result["score"],
                },
                "computed_at": datetime.now(UTC),
            }
        )

    for start in range(0, len(score_rows), 500):
        batch = score_rows[start : start + 500]
        statement = pg_insert(TraderScore).values(batch)
        statement = statement.on_conflict_do_update(
            index_elements=[TraderScore.lead_portfolio_id, TraderScore.config_version],
            set_={
                "score": statement.excluded.score,
                "band": statement.excluded.band,
                "confidence": statement.excluded.confidence,
                "rankable": statement.excluded.rankable,
                "hard_flags": statement.excluded.hard_flags,
                "breakdown": statement.excluded.breakdown,
                "computed_at": statement.excluded.computed_at,
            },
        )
        await db.execute(statement)
    await db.commit()

    summary = {
        "config_version": config.version,
        "traders": len(score_rows),
        "rankable": sum(1 for row in score_rows if row["rankable"]),
        "scored": sum(1 for row in score_rows if row["score"] is not None),
        "bands": {},
        "duration_seconds": round(time.monotonic() - started, 2),
    }
    for row in score_rows:
        key = row["band"] or "none"
        summary["bands"][key] = summary["bands"].get(key, 0) + 1
    logger.info("build scores: %s", summary)
    return summary
