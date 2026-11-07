"""L0 — Universe scan: quét list PUBLIC + SIGNAL (chỉ 90D)."""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.collection_log import CollectionLog
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
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
        for portfolio_type in portfolio_types:
            page = 1
            fetched_type = 0
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
                archive.append(
                    f"list-{portfolio_type.lower()}",
                    f"page-{page:04d}",
                    page_data.items,
                    meta={
                        "endpoint": "/home-page/query-list",
                        "portfolio_type": portfolio_type,
                        "page": page,
                        "total": page_data.total,
                        "collected_at": collected_at.isoformat(),
                    },
                    at=collected_at,
                )
                await db.commit()

                if not page_data.items or fetched_type >= page_data.total:
                    break
                page += 1
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
