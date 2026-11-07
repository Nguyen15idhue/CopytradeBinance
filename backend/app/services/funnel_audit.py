"""Audit false negative cho trader excluded (mẫu nhỏ, chỉ đọc thêm 2 endpoint)."""

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_log import CollectionLog
from app.models.performance import PerformanceMetric
from app.models.snapshot import PortfolioSnapshot
from app.models.universe import TraderUniverse
from app.services.collector.parsers import ms_to_dt
from app.services.funnel import fnum

logger = logging.getLogger(__name__)

AUDIT_LAYER = "A1"
WATCH_MIN_TOTAL_ORDERS = 20
WATCH_MIN_AUM = 5_000.0


def watch_eligible(
    detail: dict[str, Any], performance: dict[str, Any], now: datetime
) -> dict[str, Any]:
    """Điều kiện Watch thực tế sau detail + performance (định nghĩa gate Phase 0)."""
    reasons: list[str] = []
    runtime_days = None
    start = fnum(detail.get("startTime"))
    if start:
        runtime_days = (now - datetime.fromtimestamp(start / 1000, tz=UTC)).days
    if detail.get("status") != "ACTIVE":
        reasons.append("not_active")
    if detail.get("isPaused") is True:
        reasons.append("paused")
    if runtime_days is None or runtime_days < 30:
        reasons.append("runtime_lt_30")
    roi = fnum(performance.get("roi"))
    pnl = fnum(performance.get("pnl"))
    win_rate = fnum(performance.get("winRate"))
    mdd = fnum(performance.get("mdd"))
    total_orders = fnum(performance.get("totalOrder"))
    aum = fnum(detail.get("aumAmount")) or fnum(detail.get("aum"))
    current = fnum(detail.get("currentCopyCount")) or 0.0
    maximum = fnum(detail.get("maxCopyCount")) or 0.0
    last_trade = ms_to_dt(detail.get("lastTradeTime"))
    if roi is None or roi <= 0:
        reasons.append("roi_le_0")
    if pnl is None or pnl <= 0:
        reasons.append("pnl_le_0")
    if win_rate is None or win_rate < 40:
        reasons.append("winrate_lt_40")
    if mdd is not None and mdd > 40:
        reasons.append("mdd_gt_40")
    if aum is None or aum < WATCH_MIN_AUM:
        reasons.append("aum_lt_5000")
    if total_orders is None or total_orders < WATCH_MIN_TOTAL_ORDERS:
        reasons.append("total_orders_lt_20")
    if maximum <= 0 or current >= maximum:
        reasons.append("no_slots")
    if last_trade is None or (now - last_trade).days > 7:
        reasons.append("no_trade_7d")
    return {"eligible": not reasons, "reasons": reasons, "runtime_days": runtime_days}


async def audit_excluded(
    adapter, db: AsyncSession, limit: int = 50, persist: bool = True
) -> dict[str, Any]:
    ids = (
        await db.execute(
            select(TraderUniverse.lead_portfolio_id)
            .where(TraderUniverse.potential_tier == "excluded")
            .order_by(TraderUniverse.lead_portfolio_id)
            .limit(limit)
        )
    ).scalars().all()
    now = datetime.now(UTC)

    async def detail_task(pid: str):
        try:
            return pid, await adapter.get_detail(pid), None
        except Exception as exc:  # noqa: BLE001
            return pid, None, str(exc)

    async def perf_task(pid: str):
        try:
            return pid, await adapter.get_performance(pid, "90D"), None
        except Exception as exc:  # noqa: BLE001
            return pid, None, str(exc)

    details, perfs = await asyncio.gather(
        asyncio.gather(*(detail_task(pid) for pid in ids)),
        asyncio.gather(*(perf_task(pid) for pid in ids)),
    )
    detail_map = {pid: data for pid, data, error in details if data is not None}
    perf_map = {pid: data for pid, data, error in perfs if data is not None}
    errors = [error for _pid, _data, error in (*details, *perfs) if error]

    results: list[dict[str, Any]] = []
    for pid in ids:
        detail = detail_map.get(pid)
        performance = perf_map.get(pid)
        if detail is None or performance is None:
            results.append({"id": pid, "eligible": None, "reasons": ["insufficient_data"]})
            continue
        checks = watch_eligible(detail, performance, now)
        results.append({"id": pid, **checks})

    eligible = sum(1 for row in results if row["eligible"] is True)
    insufficient = sum(1 for row in results if row["eligible"] is None)
    sample = len(ids)
    evaluated = sample - insufficient
    summary = {
        "sample": sample,
        "evaluated": evaluated,
        "insufficient_data": insufficient,
        "false_negative": eligible,
        "false_negative_rate": round(eligible / evaluated * 100, 2) if evaluated else None,
        "errors": len(errors),
        "error_samples": errors[:5],
        "sample_details": results[:10],
    }

    if persist and detail_map:
        moment = now.replace(minute=0, second=0, microsecond=0)
        rows = [
            {
                "lead_portfolio_id": pid,
                "collected_at": moment,
                "collected_hour": moment,
                "source": "detail",
                "raw": detail,
                "schema_version": 1,
            }
            for pid, detail in detail_map.items()
        ]
        insert = pg_insert(PortfolioSnapshot).values(rows).on_conflict_do_nothing()
        await db.execute(insert)
        perf_rows = [
            {
                "lead_portfolio_id": pid,
                "time_range": "90D",
                "collected_at": moment,
                "roi": _decimal(data.get("roi")),
                "pnl": _decimal(data.get("pnl")),
                "mdd": _decimal(data.get("mdd")),
                "copier_pnl": _decimal(data.get("copierPnl")),
                "win_rate": _decimal(data.get("winRate")),
                "win_orders": data.get("winOrders"),
                "total_orders": data.get("totalOrder"),
                "sharpe": _decimal(data.get("sharpRatio")),
                "raw": {"source": "bapi", "endpoint": "performance", "window": "90D",
                        "payload": data},
            }
            for pid, data in perf_map.items()
        ]
        if perf_rows:
            insert = pg_insert(PerformanceMetric).values(perf_rows).on_conflict_do_nothing()
            await db.execute(insert)
        db.add(
            CollectionLog(
                layer=AUDIT_LAYER,
                status="success",
                finished_at=datetime.now(UTC),
                requests=sample * 2,
                items_ok=evaluated,
                error_count=len(errors),
                detail=summary,
            )
        )
        await db.commit()

    return summary


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError):
        return None
