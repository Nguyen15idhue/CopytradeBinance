"""L0 — Universe scan: quét list PUBLIC + SIGNAL (chỉ 90D)."""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.collection_log import CollectionLog
from app.models.performance import PerformanceMetric
from app.models.snapshot import PortfolioSnapshot
from app.models.tier_history import TierHistory
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.services.funnel import (
    TIER_RANK,
    annotate_pre_score,
    apply_total_order_demotion,
    evaluate_item,
)
from app.services.storage.raw import RawArchive

logger = logging.getLogger(__name__)

LAYER = "L0"
PORTFOLIO_TYPES = ("PUBLIC", "SIGNAL")
MAX_PAGES = 1000


@dataclass
class ScanResult:
    total: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    duplicates: int = 0
    pages: int = 0
    requests: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    skipped: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_type": self.by_type,
            "duplicates": self.duplicates,
            "pages": self.pages,
            "requests": self.requests,
            "errors": self.errors[:10],
            "duration_seconds": round(self.duration_seconds, 2),
            "skipped": self.skipped,
        }


def dedupe(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for item in items:
        portfolio_id = item.get("leadPortfolioId")
        if not portfolio_id:
            continue
        if portfolio_id in seen:
            duplicates += 1
            continue
        seen[portfolio_id] = item
    return list(seen.values()), duplicates


def _ms_to_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


async def _upsert_traders(db: AsyncSession, items: list[dict[str, Any]]) -> None:
    if not items:
        return
    rows = [
        {
            "lead_portfolio_id": item["leadPortfolioId"],
            "nickname": item.get("nickname"),
            "avatar_url": item.get("avatarUrl"),
            "portfolio_type": item.get("portfolioType"),
            "start_time": _ms_to_datetime(item.get("startTime")),
        }
        for item in items
    ]
    statement = pg_insert(Trader).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=[Trader.lead_portfolio_id],
        set_={
            "nickname": statement.excluded.nickname,
            "avatar_url": statement.excluded.avatar_url,
            "portfolio_type": statement.excluded.portfolio_type,
            "start_time": statement.excluded.start_time,
        },
    )
    await db.execute(statement)


async def _insert_snapshots(
    db: AsyncSession, items: list[dict[str, Any]], collected_at: datetime
) -> None:
    if not items:
        return
    collected_hour = collected_at.replace(minute=0, second=0, microsecond=0)
    rows = [
        {
            "lead_portfolio_id": item["leadPortfolioId"],
            "collected_at": collected_at,
            "collected_hour": collected_hour,
            "source": "list",
            "raw": item,
            "schema_version": 1,
        }
        for item in items
    ]
    statement = pg_insert(PortfolioSnapshot).values(rows)
    statement = statement.on_conflict_do_nothing(
        index_elements=[
            PortfolioSnapshot.lead_portfolio_id,
            PortfolioSnapshot.collected_hour,
            PortfolioSnapshot.source,
        ]
    )
    await db.execute(statement)


async def scan_universe(
    adapter: Any,
    db: AsyncSession,
    archive: RawArchive | None = None,
    time_range: str = "90D",
    portfolio_types: tuple[str, ...] = PORTFOLIO_TYPES,
    max_pages: int = MAX_PAGES,
) -> ScanResult:
    settings = get_settings()
    started = time.monotonic()
    archive = archive or RawArchive()
    collected_at = datetime.now(UTC)
    result = ScanResult()

    log = CollectionLog(layer=LAYER, status="running", started_at=collected_at)
    db.add(log)
    await db.commit()
    log_id = log.id

    try:
        seen_ids: set[str] = set()
        scan_id = uuid4()
        for portfolio_type in portfolio_types:
            page = 1
            fetched_type = 0
            raw_items: list[dict[str, Any]] = []
            while page <= max_pages:
                if settings.collector_kill_switch:
                    result.skipped = True
                    break
                page_data = await adapter.list_traders(time_range, page, portfolio_type)
                result.pages += 1
                result.requests += 1
                unique_items, duplicates = dedupe(page_data.items)
                fresh_items = [
                    item
                    for item in unique_items
                    if item.get("leadPortfolioId") and item["leadPortfolioId"] not in seen_ids
                ]
                duplicates += len(unique_items) - len(fresh_items)
                seen_ids.update(item["leadPortfolioId"] for item in fresh_items)
                result.duplicates += duplicates
                result.by_type[portfolio_type] = result.by_type.get(portfolio_type, 0) + len(
                    fresh_items
                )
                result.total += len(fresh_items)
                fetched_type += len(page_data.items)

                await _upsert_traders(db, fresh_items)
                await _insert_snapshots(db, fresh_items, collected_at)
                raw_items.extend(page_data.items)
                await db.commit()

                if not page_data.items or fetched_type >= page_data.total:
                    break
                page += 1
            if raw_items:
                await archive.write_bundle(
                    db,
                    f"list-{portfolio_type.lower()}",
                    raw_items,
                    meta={
                        "endpoint": "/home-page/query-list",
                        "portfolio_type": portfolio_type,
                        "total": fetched_type,
                        "pages": result.pages,
                        "collected_at": collected_at.isoformat(),
                    },
                    at=collected_at,
                    scan_id=scan_id,
                    layer=LAYER,
                )
            if result.skipped:
                break

        log.status = "skipped" if result.skipped else "success"
    except Exception as exc:
        await db.rollback()
        log.status = "failed"
        result.errors.append(str(exc))
        raise
    finally:
        result.duration_seconds = time.monotonic() - started
        record = await db.get(CollectionLog, log_id)
        if record is not None:
            if result.errors:
                record.status = "failed"
            elif result.skipped:
                record.status = "skipped"
            else:
                record.status = "success"
            record.finished_at = datetime.now(UTC)
            record.pages = result.pages
            record.requests = result.requests
            record.items_ok = result.total
            record.error_count = len(result.errors)
            record.detail = result.as_dict()
            await db.commit()
        logger.info("L0 scan xong: %s", result.as_dict())

    return result


async def latest_scan_log(db: AsyncSession) -> CollectionLog | None:
    result = await db.execute(
        select(CollectionLog).where(CollectionLog.layer == LAYER).order_by(CollectionLog.id.desc())
    )
    return result.scalars().first()


async def recompute_universe(db: AsyncSession, aum_min: int | None = None) -> dict[str, Any]:
    """Tính lại tier/pre_score từ list snapshot mới nhất. Idempotent."""
    settings = get_settings()
    started = time.monotonic()
    now = datetime.now(UTC)
    now_ms = int(now.timestamp() * 1000)
    threshold = aum_min or settings.aum_preset

    latest = (
        select(
            PortfolioSnapshot.lead_portfolio_id.label("portfolio_id"),
            func.max(PortfolioSnapshot.collected_at).label("collected_at"),
        )
        .where(PortfolioSnapshot.source == "list")
        .group_by(PortfolioSnapshot.lead_portfolio_id)
        .subquery()
    )
    snapshots = (
        await db.execute(
            select(PortfolioSnapshot).join(
                latest,
                (PortfolioSnapshot.lead_portfolio_id == latest.c.portfolio_id)
                & (PortfolioSnapshot.collected_at == latest.c.collected_at),
            )
        )
    ).scalars().all()

    items: list[dict[str, Any]] = []
    for snapshot in snapshots:
        item = dict(snapshot.raw or {})
        item.setdefault("leadPortfolioId", snapshot.lead_portfolio_id)
        items.append(item)
    annotate_pre_score(items, now_ms)

    existing = dict(
        (
            await db.execute(
                select(TraderUniverse.lead_portfolio_id, TraderUniverse.potential_tier)
            )
        ).all()
    )

    latest_perf = (
        select(
            PerformanceMetric.lead_portfolio_id.label("portfolio_id"),
            func.max(PerformanceMetric.collected_at).label("collected_at"),
        )
        .where(PerformanceMetric.time_range == "90D")
        .group_by(PerformanceMetric.lead_portfolio_id)
        .subquery()
    )
    total_orders_map = {
        portfolio_id: total_orders
        for portfolio_id, total_orders in (
            await db.execute(
                select(
                    PerformanceMetric.lead_portfolio_id,
                    PerformanceMetric.total_orders,
                ).join(
                    latest_perf,
                    and_(
                        PerformanceMetric.lead_portfolio_id == latest_perf.c.portfolio_id,
                        PerformanceMetric.collected_at == latest_perf.c.collected_at,
                    ),
                )
            )
        ).all()
    }

    counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    for item in items:
        evaluated = evaluate_item(item, now_ms, aum_min=float(threshold))
        tier = apply_total_order_demotion(
            evaluated["tier"], total_orders_map.get(item["leadPortfolioId"])
        )
        reasons = list(evaluated["reasons"])
        if tier != evaluated["tier"]:
            reasons.append("total_orders_lt_threshold")
        counts[tier] = counts.get(tier, 0) + 1
        portfolio_id = item["leadPortfolioId"]
        rows.append(
            {
                "lead_portfolio_id": portfolio_id,
                "potential_tier": tier,
                "pre_score": item["pre_score"],
                "filter_reasons": reasons,
                "deep_fetch_status": "skipped" if tier == "excluded" else "pending",
            }
        )
        old_tier = existing.get(portfolio_id)
        if old_tier != tier:
            history.append(
                {
                    "lead_portfolio_id": portfolio_id,
                    "old_tier": old_tier,
                    "new_tier": tier,
                    "pre_score": item["pre_score"],
                    "reasons": reasons,
                }
            )

    for start in range(0, len(rows), 2000):
        statement = pg_insert(TraderUniverse).values(rows[start : start + 2000])
        statement = statement.on_conflict_do_update(
            index_elements=[TraderUniverse.lead_portfolio_id],
            set_={
                "potential_tier": statement.excluded.potential_tier,
                "pre_score": statement.excluded.pre_score,
                "filter_reasons": statement.excluded.filter_reasons,
                "updated_at": func.now(),
            },
        )
        await db.execute(statement)

    if history:
        for start in range(0, len(history), 1000):
            await db.execute(pg_insert(TierHistory).values(history[start : start + 1000]))
    await db.commit()

    watch_total = sum(counts.get(name, 0) for name in ("watch", "qualified_upper", "high_upper"))
    return {
        "total": len(items),
        "watch_total": watch_total,
        "counts": counts,
        "changed": len(history),
        "aum_min": threshold,
        "cohort": "all",
        "duration_seconds": round(time.monotonic() - started, 2),
        "tier_rank": TIER_RANK,
    }
