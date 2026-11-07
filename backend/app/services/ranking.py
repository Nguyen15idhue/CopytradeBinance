"""3 bảng ranking: Overall, Low Risk, Consistency + snapshot."""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ranking_snapshot import RankingSnapshot
from app.models.scoring_config import ScoringConfig
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse

logger = logging.getLogger(__name__)

TOP_N = 50


def _candidate(score_row, metric_row, tier: str, nickname: str | None) -> dict[str, Any]:
    metrics = metric_row.metrics or {}
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    component = (score_row.breakdown or {}).get("components", {})
    return {
        "id": score_row.lead_portfolio_id,
        "nickname": nickname,
        "tier": tier,
        "score": float(score_row.score) if score_row.score is not None else None,
        "band": score_row.band,
        "confidence": float(score_row.confidence) if score_row.confidence is not None else None,
        "risk_level": metric_row.risk_level,
        "roi_90d": float(published["roi"]) if published.get("roi") is not None else None,
        "mdd_90d": float(published["mdd"]) if published.get("mdd") is not None else None,
        "sharpe": float(published["sharpe"]) if published.get("sharpe") is not None else None,
        "max_leverage": float(derived["max_leverage"])
        if derived.get("max_leverage") is not None
        else None,
        "runtime_days": metrics.get("runtime_days"),
        "consistency_score": (component.get("consistency") or {}).get("score"),
        "rankable": score_row.rankable,
    }


def select_boards(candidates: list[dict[str, Any]], top_n: int = TOP_N) -> dict[str, list]:
    rankable = [row for row in candidates if row["rankable"] and row["score"] is not None]
    overall = sorted(rankable, key=lambda row: row["score"], reverse=True)[:top_n]

    low_risk = [
        row
        for row in rankable
        if (row["runtime_days"] or 0) >= 90
        and row["mdd_90d"] is not None
        and row["mdd_90d"] <= 20
        and (row["max_leverage"] is None or row["max_leverage"] <= 5)
        and (row["confidence"] or 0) >= 0.8
    ]
    low_risk = sorted(low_risk, key=lambda row: row["score"], reverse=True)[:top_n]

    consistency = [
        row
        for row in rankable
        if (row["runtime_days"] or 0) >= 90 and row["consistency_score"] is not None
    ]
    consistency = sorted(
        consistency, key=lambda row: row["consistency_score"], reverse=True
    )[:top_n]

    return {"overall": overall, "low_risk": low_risk, "consistency": consistency}


async def build_rankings(db: AsyncSession, top_n: int = TOP_N) -> dict[str, Any]:
    started = time.monotonic()
    config = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    version = config.version if config else 1

    rows = (
        await db.execute(
            select(TraderScore, TraderMetric, TraderUniverse.potential_tier, Trader.nickname)
            .join(TraderMetric, TraderMetric.lead_portfolio_id == TraderScore.lead_portfolio_id)
            .join(TraderUniverse, TraderUniverse.lead_portfolio_id == TraderScore.lead_portfolio_id)
            .join(Trader, Trader.lead_portfolio_id == TraderScore.lead_portfolio_id)
            .where(TraderScore.config_version == version)
        )
    ).all()

    candidates = [_candidate(*row) for row in rows]
    boards = select_boards(candidates, top_n=top_n)

    moment = datetime.now(UTC)
    for board, items in boards.items():
        db.add(
            RankingSnapshot(
                board=board,
                config_version=version,
                items=items,
                collected_at=moment,
            )
        )
    await db.commit()

    summary = {
        "config_version": version,
        "candidates": len(candidates),
        "boards": {board: len(items) for board, items in boards.items()},
        "top_overall": [row["id"] for row in boards["overall"][:5]],
        "duration_seconds": round(time.monotonic() - started, 2),
    }
    logger.info("build rankings: %s", summary)
    return summary
