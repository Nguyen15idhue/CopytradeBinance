"""L2–L4 — Deep fetch có chọn lọc."""

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_log import CollectionLog
from app.models.performance import PerformanceMetric
from app.models.tier_history import TierHistory
from app.models.universe import TraderUniverse

logger = logging.getLogger(__name__)

WINDOWS = ("7D", "30D", "90D", "180D")
WATCH_TIERS = ("watch", "qualified_upper", "high_upper")

# HF04: không đủ mẫu thì hạ tier tương ứng.
DEMOTE_RULES = {
    "high_upper": ("qualified_upper", 100),
    "qualified_upper": ("watch", 50),
}


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def _fetch_one(
    adapter, portfolio_id: str, window: str
) -> tuple[str, str, dict | None, str | None]:
    try:
        data = await adapter.get_performance(portfolio_id, window)
        return portfolio_id, window, data, None
    except Exception as exc:  # noqa: BLE001 - ghi lỗi theo từng request
        return portfolio_id, window, None, str(exc)


async def fetch_performance_for_watch(
    adapter,
    db: AsyncSession,
    collected_at: datetime | None = None,
    portfolio_ids: list[str] | None = None,
) -> dict[str, Any]:
    moment = (collected_at or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    statement = (
        select(TraderUniverse.lead_portfolio_id, TraderUniverse.potential_tier)
        .where(TraderUniverse.potential_tier.in_(WATCH_TIERS))
        .order_by(TraderUniverse.potential_tier, TraderUniverse.pre_score.desc().nullslast())
    )
    if portfolio_ids:
        statement = statement.where(TraderUniverse.lead_portfolio_id.in_(portfolio_ids))
    targets = (await db.execute(statement)).all()

    log = CollectionLog(layer="L2", status="running")
    db.add(log)
    await db.commit()
    log_id = log.id

    results = await asyncio.gather(
        *(
            _fetch_one(adapter, portfolio_id, window)
            for portfolio_id, _tier in targets
            for window in WINDOWS
        )
    )

    by_trader: dict[str, dict[str, dict]] = {}
    errors: list[str] = []
    for portfolio_id, window, data, error in results:
        if error or data is None:
            errors.append(f"{portfolio_id}/{window}: {error or 'empty'}")
            continue
        by_trader.setdefault(portfolio_id, {})[window] = data

    rows: list[dict[str, Any]] = []
    for portfolio_id, windows in by_trader.items():
        for window, data in windows.items():
            rows.append(
                {
                    "lead_portfolio_id": portfolio_id,
                    "time_range": window,
                    "collected_at": moment,
                    "roi": _decimal(data.get("roi")),
                    "pnl": _decimal(data.get("pnl")),
                    "mdd": _decimal(data.get("mdd")),
                    "copier_pnl": _decimal(data.get("copierPnl")),
                    "win_rate": _decimal(data.get("winRate")),
                    "win_orders": _int(data.get("winOrders")),
                    "total_orders": _int(data.get("totalOrder")),
                    "sharpe": _decimal(data.get("sharpRatio")),
                    "raw": {
                        "source": "bapi",
                        "endpoint": "performance",
                        "window": window,
                        "collectedAt": moment.isoformat(),
                        "payload": data,
                    },
                }
            )

    for start in range(0, len(rows), 1000):
        batch = rows[start : start + 1000]
        statement = pg_insert(PerformanceMetric).values(batch)
        statement = statement.on_conflict_do_update(
            index_elements=[
                PerformanceMetric.lead_portfolio_id,
                PerformanceMetric.time_range,
                PerformanceMetric.collected_at,
            ],
            set_={
                "roi": statement.excluded.roi,
                "pnl": statement.excluded.pnl,
                "mdd": statement.excluded.mdd,
                "copier_pnl": statement.excluded.copier_pnl,
                "win_rate": statement.excluded.win_rate,
                "win_orders": statement.excluded.win_orders,
                "total_orders": statement.excluded.total_orders,
                "sharpe": statement.excluded.sharpe,
                "raw": statement.excluded.raw,
            },
        )
        await db.execute(statement)

    demotions = _apply_total_order_rules(by_trader, dict(targets))
    for portfolio_id, (old_tier, new_tier, total_orders) in demotions.items():
        row = await db.get(TraderUniverse, portfolio_id)
        pre_score = None
        if row is not None:
            row.potential_tier = new_tier
            pre_score = row.pre_score
        db.add(
            TierHistory(
                lead_portfolio_id=portfolio_id,
                old_tier=old_tier,
                new_tier=new_tier,
                reasons=["total_orders_lt_threshold"],
                pre_score=pre_score,
            )
        )
        logger.info(
            "Hạ tier %s: %s → %s (totalOrder=%s)",
            portfolio_id,
            old_tier,
            new_tier,
            total_orders,
        )

    record = await db.get(CollectionLog, log_id)
    if record is not None:
        record.status = "success"
        record.finished_at = datetime.now(UTC)
        record.pages = len(WINDOWS)
        record.requests = len(results)
        record.items_ok = len(rows)
        record.error_count = len(errors)
        record.detail = {
            "traders": len(by_trader),
            "targets": len(targets),
            "metrics_saved": len(rows),
            "errors": errors[:10],
            "demotions": len(demotions),
        }
    await db.commit()
    return {
        "targets": len(targets),
        "traders": len(by_trader),
        "metrics_saved": len(rows),
        "errors": len(errors),
        "demotions": len(demotions),
        "collected_at": moment.isoformat(),
    }


def _apply_total_order_rules(
    by_trader: dict[str, dict[str, dict]], tiers: dict[str, str]
) -> dict[str, tuple[str, str, int]]:
    changes: dict[str, tuple[str, str, int]] = {}
    for portfolio_id, tier in tiers.items():
        rule = DEMOTE_RULES.get(tier)
        if rule is None:
            continue
        performance = by_trader.get(portfolio_id, {}).get("90D")
        if not performance:
            continue
        total_orders = _int(performance.get("totalOrder"))
        if total_orders is None:
            continue
        new_tier, threshold = rule
        if total_orders < threshold:
            changes[portfolio_id] = (tier, new_tier, total_orders)
    return changes


async def count_by_tier(db: AsyncSession) -> dict[str, int]:
    rows = (
        await db.execute(
            select(TraderUniverse.potential_tier, func.count()).group_by(
                TraderUniverse.potential_tier
            )
        )
    ).all()
    return {tier: count for tier, count in rows}
