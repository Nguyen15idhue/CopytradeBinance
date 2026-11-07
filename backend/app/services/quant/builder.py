"""Tính và lưu trader_metrics từ dữ liệu đã thu thập."""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.performance import PerformanceMetric
from app.models.position import Position
from app.models.snapshot import PortfolioSnapshot
from app.models.trade import Trade
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.transfer import Transfer
from app.models.universe import TraderUniverse
from app.services.quant import metrics as qm
from app.services.quant.confidence import compute_confidence

logger = logging.getLogger(__name__)
BATCH = 500

WINDOW_COLUMN_MAP: dict[str, dict[str, str]] = {
    "7D": {
        "roi": "roi_7d",
        "mdd": "mdd_7d",
        "sharpe": "sharpe_7d",
        "copier_pnl": "copier_pnl_7d",
        "win_rate_order": "win_rate_order_7d",
    },
    "30D": {
        "roi": "roi_30d",
        "mdd": "mdd_30d",
        "sharpe": "sharpe_30d",
        "copier_pnl": "copier_pnl_30d",
        "win_rate_order": "win_rate_order_30d",
    },
    "180D": {
        "roi": "roi_180d",
        "mdd": "mdd_180d",
        "sharpe": "sharpe_180d",
        "copier_pnl": "copier_pnl_180d",
        "win_rate_order": "win_rate_order_180d",
    },
}
WINDOW_UPSERT_COLUMNS = tuple(
    column for mapping in WINDOW_COLUMN_MAP.values() for column in mapping.values()
)


def _value(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _latest_by_lead(rows: list[Any], key=lambda row: row.lead_portfolio_id) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for row in rows:
        key_value = key(row)
        current = latest.get(key_value)
        if current is None or row.collected_at >= current.collected_at:
            latest[key_value] = row
    return latest


async def rebuild_metrics(
    db: AsyncSession,
    portfolio_ids: list[str] | None = None,
    include_excluded: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    now = datetime.now(UTC)

    target_statement = select(
        TraderUniverse.lead_portfolio_id,
        TraderUniverse.potential_tier,
        Trader.start_time,
    ).join(Trader, Trader.lead_portfolio_id == TraderUniverse.lead_portfolio_id)
    if portfolio_ids:
        target_statement = target_statement.where(
            TraderUniverse.lead_portfolio_id.in_(portfolio_ids)
        )
    elif not include_excluded:
        target_statement = target_statement.where(
            TraderUniverse.potential_tier != "excluded"
        )
    targets = (await db.execute(target_statement)).all()
    ids = [row.lead_portfolio_id for row in targets]
    if not ids:
        return {"traders": 0, "saved": 0, "duration_seconds": 0.0}

    performance_rows = (
        await db.execute(
            select(PerformanceMetric)
            .where(PerformanceMetric.lead_portfolio_id.in_(ids))
            .order_by(PerformanceMetric.collected_at)
        )
    ).scalars().all()
    performance_by_lead: dict[str, dict[str, dict[str, Any]]] = {}
    latest_perf_at: dict[str, datetime] = {}
    for row in performance_rows:
        bucket = performance_by_lead.setdefault(row.lead_portfolio_id, {})
        bucket[row.time_range] = {
            "roi": _value(row.roi),
            "pnl": _value(row.pnl),
            "mdd": _value(row.mdd),
            "sharpe": _value(row.sharpe),
            "copier_pnl": _value(row.copier_pnl),
            "win_orders": row.win_orders,
            "total_orders": row.total_orders,
            "win_rate": _value(row.win_rate),
        }
        current = latest_perf_at.get(row.lead_portfolio_id)
        if current is None or row.collected_at > current:
            latest_perf_at[row.lead_portfolio_id] = row.collected_at

    detail_rows = (
        await db.execute(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.lead_portfolio_id.in_(ids),
                PortfolioSnapshot.source == "detail",
            )
            .order_by(PortfolioSnapshot.collected_at)
        )
    ).scalars().all()
    detail_by_lead = _latest_by_lead(list(detail_rows))

    list_rows = (
        await db.execute(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.lead_portfolio_id.in_(ids),
                PortfolioSnapshot.source.in_(("list", "demo")),
            )
            .order_by(PortfolioSnapshot.collected_at)
        )
    ).scalars().all()
    list_by_lead = _latest_by_lead(list(list_rows))

    position_rows = (
        await db.execute(
            select(
                Position.lead_portfolio_id,
                Position.symbol,
                Position.side,
                Position.leverage,
                Position.isolated,
                Position.opened_at,
                Position.closed_at,
                Position.closing_pnl,
                Position.roi,
                Position.max_open_interest,
            ).where(Position.lead_portfolio_id.in_(ids))
        )
    ).all()

    trade_rows = (
        await db.execute(
            select(
                Trade.lead_portfolio_id,
                Trade.quantity,
                Trade.fee,
                Trade.realized_profit,
                Trade.trade_time,
            ).where(Trade.lead_portfolio_id.in_(ids))
        )
    ).all()

    transfer_rows = (
        await db.execute(
            select(
                Transfer.lead_portfolio_id,
                Transfer.amount,
                Transfer.trans_type,
            ).where(Transfer.lead_portfolio_id.in_(ids))
        )
    ).all()

    continuity_rows = (
        await db.execute(
            text(
                "select lead_portfolio_id, count(distinct date(collected_at)) as days "
                "from portfolio_snapshots where source='list' "
                "and collected_at >= now() - interval '7 days' "
                "and lead_portfolio_id = any(:ids) group by lead_portfolio_id"
            ),
            {"ids": ids},
        )
    ).all()
    continuity = {row[0]: int(row[1]) for row in continuity_rows}

    def group(rows, key: str) -> dict[str, list[Any]]:
        grouped: dict[str, list[Any]] = {}
        for row in rows:
            grouped.setdefault(getattr(row, key), []).append(row)
        return grouped

    positions_by_lead = group(position_rows, "lead_portfolio_id")
    trades_by_lead = group(trade_rows, "lead_portfolio_id")
    transfers_by_lead = group(transfer_rows, "lead_portfolio_id")

    rows_to_save: list[dict[str, Any]] = []
    for target in targets:
        pid = target.lead_portfolio_id
        performance = performance_by_lead.get(pid, {})
        published = qm.published_metrics(performance)
        detail = detail_by_lead.get(pid)
        detail_raw = detail.raw if detail else {}
        list_raw = (list_by_lead.get(pid).raw or {}) if list_by_lead.get(pid) else {}

        aum = qm._f(detail_raw.get("aumAmount")) or qm._f(list_raw.get("aum"))
        copy_aum = qm._f(detail_raw.get("copyAum"))
        if copy_aum is None:
            copy_aum = qm._f(list_raw.get("copyAum"))
        current_copiers = detail_raw.get("currentCopyCount")
        if current_copiers is None:
            current_copiers = list_raw.get("currentCopyCount")
        max_copiers = detail_raw.get("maxCopyCount")
        if max_copiers is None:
            max_copiers = list_raw.get("maxCopyCount")

        start_time = detail_raw.get("startTime")
        if start_time:
            runtime_days = (now - datetime.fromtimestamp(int(start_time) / 1000, tz=UTC)).days
        elif target.start_time is not None:
            runtime_days = (now - target.start_time).total_seconds() / 86_400
        else:
            runtime_days = None

        positions = qm.position_metrics(
            [dict(row._mapping) for row in positions_by_lead.get(pid, [])]
        )
        trades = qm.trade_metrics(
            [dict(row._mapping) for row in trades_by_lead.get(pid, [])],
            pnl_90d=published["90D"]["pnl"],
        )
        transfers = qm.transfer_metrics(
            [dict(row._mapping) for row in transfers_by_lead.get(pid, [])]
        )
        derived = qm.ratio_metrics(
            published,
            positions,
            aum,
            copy_aum,
            current_copiers,
            published["90D"]["copier_pnl"],
        )
        derived["positive_days_pct"] = qm.positive_days_pct(list_raw.get("chartItems"))
        derived["roi_stability"] = qm.roi_stability(published)

        perf_time = latest_perf_at.get(pid)
        freshness_minutes = (
            (now - perf_time).total_seconds() / 60 if perf_time is not None else None
        )
        fields = {
            "roi": published["90D"]["roi"],
            "pnl": published["90D"]["pnl"],
            "mdd": published["90D"]["mdd"],
            "sharpe": published["90D"]["sharpe"],
            "win_rate": published["90D"]["win_rate_order"],
            "total_orders": published["90D"]["total_orders"],
            "aum": aum,
            "copy_aum": copy_aum,
            "current_copiers": current_copiers,
            "runtime_days": runtime_days,
            "max_leverage": positions["max_leverage"],
            "position_win_rate": positions["position_win_rate"],
        }
        confidence = compute_confidence(
            fields, runtime_days, freshness_minutes, continuity.get(pid, 0)
        )

        metrics = {
            "published": published,
            "profile": {
                "aum": aum,
                "copy_aum": copy_aum,
                "margin_balance": qm._f(detail_raw.get("marginBalance")),
                "current_copiers": current_copiers,
                "max_copiers": max_copiers,
                "total_copiers": detail_raw.get("totalCopyCount"),
                "profit_sharing_rate": qm._f(detail_raw.get("profitSharingRate")),
                "favorite_count": detail_raw.get("favoriteCount"),
                "status": detail_raw.get("status") or list_raw.get("status"),
                "portfolio_type": detail_raw.get("portfolioType")
                or list_raw.get("portfolioType"),
            },
            "derived": {**positions, **trades, **transfers, **derived},
            "confidence": confidence,
            "runtime_days": runtime_days,
            "freshness_minutes": round(freshness_minutes, 2)
            if freshness_minutes is not None
            else None,
            "benchmark_return": None,
            "excess_return": None,
            "provenance": {
                "performance_at": perf_time.isoformat() if perf_time else None,
                "detail_at": detail.collected_at.isoformat() if detail else None,
                "positions": positions["positions_count"],
                "trades": trades["total_fills"],
                "transfers": transfers["transfers_count"],
            },
        }
        metrics["flags"] = qm.missing_flags(metrics)

        window_columns: dict[str, Any] = {}
        for window, mapping in WINDOW_COLUMN_MAP.items():
            window_data = published.get(window) or {}
            for source_key, column_name in mapping.items():
                window_columns[column_name] = window_data.get(source_key)

        rows_to_save.append(
            {
                "lead_portfolio_id": pid,
                "roi_90d": published["90D"]["roi"],
                "mdd_90d": published["90D"]["mdd"],
                "sharpe_90d": published["90D"]["sharpe"],
                "win_rate_order_90d": published["90D"]["win_rate_order"],
                "total_orders_90d": published["90D"]["total_orders"],
                "copier_pnl_90d": published["90D"]["copier_pnl"],
                **window_columns,
                "aum": aum,
                "copy_aum": copy_aum,
                "current_copiers": current_copiers,
                "runtime_days": round(runtime_days, 2) if runtime_days is not None else None,
                "max_leverage": positions["max_leverage"],
                "avg_leverage": positions["avg_leverage"],
                "position_win_rate": positions["position_win_rate"],
                "profit_factor": positions["profit_factor"],
                "fee_drag_pct": trades["fee_drag_pct"],
                "confidence": confidence["value"],
                "low_sample": derived["low_sample"],
                "metrics": metrics,
                "computed_at": now,
            }
        )

    for start in range(0, len(rows_to_save), BATCH):
        batch = rows_to_save[start : start + BATCH]
        statement = pg_insert(TraderMetric).values(batch)
        statement = statement.on_conflict_do_update(
            index_elements=[TraderMetric.lead_portfolio_id],
            set_={
                column: getattr(statement.excluded, column)
                for column in (
                    "roi_90d",
                    "mdd_90d",
                    "sharpe_90d",
                    "win_rate_order_90d",
                    "total_orders_90d",
                    "copier_pnl_90d",
                    "aum",
                    "copy_aum",
                    "current_copiers",
                    "runtime_days",
                    "max_leverage",
                    "avg_leverage",
                    "position_win_rate",
                    "profit_factor",
                    "fee_drag_pct",
                    "confidence",
                    "low_sample",
                    "metrics",
                    "computed_at",
                    *WINDOW_UPSERT_COLUMNS,
                )
            },
        )
        await db.execute(statement)
    await db.commit()

    result = {
        "traders": len(ids),
        "saved": len(rows_to_save),
        "duration_seconds": round(time.monotonic() - started, 2),
    }
    logger.info("rebuild metrics: %s", result)
    return result
