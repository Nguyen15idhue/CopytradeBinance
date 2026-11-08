"""Retention raw archive (kế hoạch 05, bước 5.0.3).

- `latest_previous`: không xoá gì; luôn giữ latest + previous.
- `audit`: nén bundle cũ hơn N ngày; xoá bundle quá hạn; đánh dấu manifest `purged`.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.raw_manifest import RawArchiveManifest
from app.services.storage.raw import RawArchive


async def run_retention(
    db: AsyncSession,
    dry_run: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    moment = now or datetime.now(UTC)
    archive = RawArchive(mode=settings.raw_archive_mode)
    mode = archive.mode

    if mode != "audit":
        return {
            "mode": mode,
            "dry_run": dry_run,
            "compressed": 0,
            "removed": 0,
            "purged_manifests": 0,
            "note": "latest_previous: giữ latest + previous, không xoá",
        }

    compress_after = settings.raw_archive_compress_after_days
    retention_days = settings.raw_archive_audit_retention_days
    cutoff_purge = moment - timedelta(days=retention_days)

    candidates: list[Path] = []
    if archive.archive_dir.exists():
        for path in sorted(archive.archive_dir.rglob("*.jsonl.gz")):
            if path.stat().st_mtime < moment.timestamp():
                candidates.append(path)

    compress_targets = [
        path
        for path in candidates
        if path.stat().st_mtime < (moment - timedelta(days=compress_after)).timestamp()
        and not path.name.endswith(".jsonl.gz.tmp")
    ]
    purge_targets = [
        path
        for path in candidates
        if path.stat().st_mtime < cutoff_purge.timestamp()
    ]

    result = {
        "mode": mode,
        "dry_run": dry_run,
        "compress_candidates": [str(p) for p in compress_targets],
        "purge_candidates": [str(p) for p in purge_targets],
        "removed": len(purge_targets),
        "removed_bytes": sum(path.stat().st_size for path in purge_targets),
        "purged_manifests": 0,
    }
    if dry_run:
        return result

    # Nén: audit đã ghi .jsonl.gz; chỉ nén file .jsonl còn sót (legacy).
    archive.compress_older_than(compress_after, now=moment)
    archive.purge_older_than(retention_days, now=moment)

    rows = (
        await db.execute(
            select(RawArchiveManifest).where(
                RawArchiveManifest.mode == "audit",
                RawArchiveManifest.status == "success",
                RawArchiveManifest.created_at < cutoff_purge,
            )
        )
    ).scalars().all()
    for row in rows:
        row.status = "purged"
        row.purged_at = moment
    if rows:
        await db.commit()
    result["purged_manifests"] = len(rows)
    return result
