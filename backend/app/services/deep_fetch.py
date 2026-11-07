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
from app.models.position import Position
from app.models.snapshot import PortfolioSnapshot
from app.models.tier_history import TierHistory
from app.models.trade import Trade
from app.models.trader import Trader
from app.models.transfer import Transfer
from app.models.universe import TraderUniverse
from app.services.collector.parsers import ms_to_dt, parse_position, parse_trade, parse_transfer

logger = logging.getLogger(__name__)

WINDOWS = ("7D", "30D", "90D", "180D")
WATCH_TIERS = ("watch", "qualified_upper", "high_upper")
DETAIL_TIERS = ("qualified_upper", "high_upper")
MAX_POSITION_PAGES = 20
MAX_TRANSFER_PAGES = 10
MAX_TRADE_PAGES = 500
TOP_WATCH_LIMIT = 200
TOP_QUALIFIED_TRADES = 50

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


async def _fetch_pages(fetch_page, portfolio_id: str, max_pages: int) -> tuple[list, str | None]:
    collected: list[dict] = []
    page = 1
    while page <= max_pages:
        try:
            result = await fetch_page(portfolio_id, page)
        except Exception as exc:  # noqa: BLE001
            return collected, str(exc)
        collected.extend(result.items)
        if not result.items or len(collected) >= result.total:
            break
        page += 1
    return collected, None


def _is_eligible(detail: dict) -> bool:
    if detail.get("status") != "ACTIVE":
        return False
    if detail.get("isPaused") is True:
        return False
    current = detail.get("currentCopyCount")
    maximum = detail.get("maxCopyCount")
    return not (maximum is not None and current is not None and current >= maximum)


async def _detail_task(adapter, portfolio_id: str):
    try:
        return portfolio_id, await adapter.get_detail(portfolio_id), None
    except Exception as exc:  # noqa: BLE001
        return portfolio_id, None, str(exc)


async def fetch_detail_and_history(
    adapter,
    db: AsyncSession,
    collected_at: datetime | None = None,
    top_watch_limit: int = TOP_WATCH_LIMIT,
    portfolio_ids: list[str] | None = None,
) -> dict[str, Any]:
    moment = (collected_at or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    if portfolio_ids:
        target_ids = list(portfolio_ids)
    else:
        qualified = (
            await db.execute(
                select(TraderUniverse.lead_portfolio_id).where(
                    TraderUniverse.potential_tier.in_(DETAIL_TIERS)
                )
            )
        ).scalars().all()
        top_watch = (
            await db.execute(
                select(TraderUniverse.lead_portfolio_id)
                .where(TraderUniverse.potential_tier == "watch")
                .order_by(TraderUniverse.pre_score.desc().nullslast())
                .limit(top_watch_limit)
            )
        ).scalars().all()
        target_ids = list(qualified) + list(top_watch)

    log = CollectionLog(layer="L3", status="running")
    db.add(log)
    await db.commit()
    log_id = log.id

    details = await asyncio.gather(*(_detail_task(adapter, pid) for pid in target_ids))
    detail_by_id = {pid: data for pid, data, error in details if data is not None}
    errors = [f"{pid}: {error}" for pid, _data, error in details if error]

    ineligible = [pid for pid, data in detail_by_id.items() if not _is_eligible(data)]
    history_targets = [pid for pid in detail_by_id if pid not in ineligible]

    position_results, transfer_results = await asyncio.gather(
        asyncio.gather(
            *(
                _fetch_pages(adapter.get_positions, pid, MAX_POSITION_PAGES)
                for pid in history_targets
            )
        ),
        asyncio.gather(
            *(
                _fetch_pages(adapter.get_transfers, pid, MAX_TRANSFER_PAGES)
                for pid in history_targets
            )
        ),
    )
    position_map: dict[str, list[dict]] = {}
    transfer_map: dict[str, list[dict]] = {}
    for pid, (items, error) in zip(history_targets, position_results, strict=True):
        position_map[pid] = items
        if error:
            errors.append(f"{pid}/positions: {error}")
    for pid, (items, error) in zip(history_targets, transfer_results, strict=True):
        transfer_map[pid] = items
        if error:
            errors.append(f"{pid}/transfers: {error}")

    snapshot_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    transfer_rows: list[dict[str, Any]] = []
    for pid, detail in detail_by_id.items():
        snapshot_rows.append(
            {
                "lead_portfolio_id": pid,
                "collected_at": moment,
                "collected_hour": moment,
                "source": "detail",
                "raw": detail,
                "schema_version": 1,
            }
        )
        for item in position_map.get(pid, []):
            parsed = parse_position(item)
            if not parsed["position_id"]:
                continue
            position_rows.append({"lead_portfolio_id": pid, **parsed})
        for item in transfer_map.get(pid, []):
            transfer_rows.append({"lead_portfolio_id": pid, **parse_transfer(item)})

    if detail_by_id:
        trader_rows = [
            {
                "lead_portfolio_id": pid,
                "nickname": detail.get("nickname"),
                "nickname_translate": detail.get("nicknameTranslate"),
                "avatar_url": detail.get("avatarUrl"),
                "portfolio_type": detail.get("portfolioType"),
                "status": detail.get("status"),
                "description": detail.get("description"),
                "start_time": ms_to_dt(detail.get("startTime")),
                "last_trade_time": ms_to_dt(detail.get("lastTradeTime")),
                "futures_type": detail.get("futuresType"),
                "init_invest_asset": detail.get("initInvestAsset"),
            }
            for pid, detail in detail_by_id.items()
        ]
        statement = pg_insert(Trader).values(trader_rows)
        statement = statement.on_conflict_do_update(
            index_elements=[Trader.lead_portfolio_id],
            set_={
                "nickname": statement.excluded.nickname,
                "nickname_translate": statement.excluded.nickname_translate,
                "avatar_url": statement.excluded.avatar_url,
                "portfolio_type": statement.excluded.portfolio_type,
                "status": statement.excluded.status,
                "description": statement.excluded.description,
                "start_time": statement.excluded.start_time,
                "last_trade_time": statement.excluded.last_trade_time,
                "futures_type": statement.excluded.futures_type,
                "init_invest_asset": statement.excluded.init_invest_asset,
                "updated_at": func.now(),
            },
        )
        await db.execute(statement)
        await _insert_ignore(db, PortfolioSnapshot, snapshot_rows)
    if position_rows:
        await _insert_ignore(db, Position, position_rows)
    if transfer_rows:
        await _insert_ignore(db, Transfer, transfer_rows)

    record = await db.get(CollectionLog, log_id)
    if record is not None:
        record.status = "success"
        record.finished_at = datetime.now(UTC)
        record.pages = 0
        record.requests = len(target_ids) + sum(
            len(position_map.get(pid, [])) + len(transfer_map.get(pid, []))
            for pid in history_targets
        )
        record.items_ok = len(detail_by_id)
        record.error_count = len(errors)
        record.detail = {
            "targets": len(target_ids),
            "detail_ok": len(detail_by_id),
            "ineligible": len(ineligible),
            "history_targets": len(history_targets),
            "positions": len(position_rows),
            "transfers": len(transfer_rows),
            "errors": errors[:10],
        }
    await db.commit()
    return {
        "targets": len(target_ids),
        "detail_ok": len(detail_by_id),
        "ineligible": len(ineligible),
        "history_targets": len(history_targets),
        "positions": len(position_rows),
        "transfers": len(transfer_rows),
        "errors": len(errors),
        "collected_at": moment.isoformat(),
    }


async def fetch_full_trades(
    adapter,
    db: AsyncSession,
    collected_at: datetime | None = None,
    top_qualified: int = TOP_QUALIFIED_TRADES,
    portfolio_ids: list[str] | None = None,
) -> dict[str, Any]:
    moment = (collected_at or datetime.now(UTC)).replace(minute=0, second=0, microsecond=0)
    if portfolio_ids:
        target_ids = list(portfolio_ids)
    else:
        high = (
            await db.execute(
                select(TraderUniverse.lead_portfolio_id).where(
                    TraderUniverse.potential_tier == "high_upper"
                )
            )
        ).scalars().all()
        top_qualified_ids = (
            await db.execute(
                select(TraderUniverse.lead_portfolio_id)
                .where(TraderUniverse.potential_tier == "qualified_upper")
                .order_by(TraderUniverse.pre_score.desc().nullslast())
                .limit(top_qualified)
            )
        ).scalars().all()
        target_ids = list(high) + list(top_qualified_ids)

    log = CollectionLog(layer="L4", status="running")
    db.add(log)
    await db.commit()
    log_id = log.id

    trade_semaphore = asyncio.Semaphore(3)

    async def fetch_one(portfolio_id: str):
        async with trade_semaphore:
            return await _fetch_pages(adapter.get_trades, portfolio_id, MAX_TRADE_PAGES)

    results = await asyncio.gather(*(fetch_one(pid) for pid in target_ids))

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    per_trader: dict[str, int] = {}
    for pid, (items, error) in zip(target_ids, results, strict=True):
        if error:
            errors.append(f"{pid}: {error}")
        per_trader[pid] = len(items)
        for item in items:
            rows.append({"lead_portfolio_id": pid, **parse_trade(item)})

    if rows:
        await _insert_ignore(db, Trade, rows)

    record = await db.get(CollectionLog, log_id)
    if record is not None:
        record.status = "success"
        record.finished_at = datetime.now(UTC)
        record.requests = sum(max(1, (count + 199) // 200) for count in per_trader.values())
        record.items_ok = len(rows)
        record.error_count = len(errors)
        record.detail = {
            "targets": len(target_ids),
            "trades": len(rows),
            "per_trader": per_trader,
            "errors": errors[:10],
        }
    await db.commit()
    return {
        "targets": len(target_ids),
        "trades": len(rows),
        "errors": len(errors),
        "collected_at": moment.isoformat(),
    }


async def _insert_ignore(db: AsyncSession, model, rows: list[dict[str, Any]]) -> None:
    for start in range(0, len(rows), 1000):
        statement = pg_insert(model).values(rows[start : start + 1000])
        statement = statement.on_conflict_do_nothing()
        await db.execute(statement)


async def count_by_tier(db: AsyncSession) -> dict[str, int]:
    rows = (
        await db.execute(
            select(TraderUniverse.potential_tier, func.count()).group_by(
                TraderUniverse.potential_tier
            )
        )
    ).all()
    return {tier: count for tier, count in rows}
