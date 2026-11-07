"""Tạo/cập nhật risk_events và risk_level từ trader_metrics."""

import logging
import time
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_event import RiskEvent
from app.models.trader_metric import TraderMetric
from app.services.risk_rules import evaluate_rules

logger = logging.getLogger(__name__)


async def rebuild_risk_events(
    db: AsyncSession, portfolio_ids: list[str] | None = None
) -> dict[str, Any]:
    started = time.monotonic()
    statement = select(TraderMetric)
    if portfolio_ids:
        statement = statement.where(TraderMetric.lead_portfolio_id.in_(portfolio_ids))
    metrics_rows = (await db.execute(statement)).scalars().all()
    ids = [row.lead_portfolio_id for row in metrics_rows]

    if ids:
        await db.execute(delete(RiskEvent).where(RiskEvent.lead_portfolio_id.in_(ids)))

    events: list[dict[str, Any]] = []
    levels: dict[str, str] = {}
    unknown_total = 0
    for row in metrics_rows:
        result = evaluate_rules(row.metrics)
        levels[row.lead_portfolio_id] = result["risk_level"]
        unknown_total += len(result["unknown"])
        for event in result["events"]:
            events.append({"lead_portfolio_id": row.lead_portfolio_id, **event})
        row.risk_level = result["risk_level"]
        row.risk_score = result.get("risk_score")
        row.risk_veto = {"reasons": result.get("veto_reasons", [])}

    if events:
        await db.execute(pg_insert(RiskEvent).values(events))
    await db.commit()

    by_severity: dict[str, int] = {}
    for event in events:
        by_severity[event["severity"]] = by_severity.get(event["severity"], 0) + 1

    summary = {
        "traders": len(ids),
        "events": len(events),
        "by_severity": by_severity,
        "risk_levels": {
            level: sum(1 for value in levels.values() if value == level)
            for level in set(levels.values())
        },
        "unknown_fields": unknown_total,
        "duration_seconds": round(time.monotonic() - started, 2),
    }
    logger.info("rebuild risk events: %s", summary)
    return summary
