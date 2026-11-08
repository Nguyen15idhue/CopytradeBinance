"""Raw archive: bundle gzip latest/previous + manifest, retention.

Spec: docs/kehoach/RAW-ARCHIVE-SPEC.md (kế hoạch 05).
"""

import gzip
import hashlib
import json
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.raw_manifest import RawArchiveManifest

MODES = ("latest_previous", "audit")


def _dump_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str) + "\n"


class RawArchive:
    def __init__(self, base_dir: str | None = None, mode: str | None = None) -> None:
        settings = get_settings()
        root = Path(base_dir or settings.raw_archive_dir)
        self.base_dir = root
        self.archive_dir = root / "archive"
        self.mode = mode or settings.raw_archive_mode

    # ---------- đường dẫn ----------

    def bundle_path(self, endpoint: str, name: str, at: datetime | None = None) -> Path:
        if self.mode == "audit":
            moment = at or datetime.now(UTC)
            return self.archive_dir / moment.strftime("%Y-%m-%d") / f"{name}.jsonl.gz"
        return self.archive_dir / endpoint / f"{name}.jsonl.gz"

    # ---------- ghi bundle ----------

    async def write_bundle(
        self,
        db: AsyncSession | None,
        endpoint: str,
        records: list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
        at: datetime | None = None,
        scan_id: UUID | None = None,
        layer: str = "L0",
    ) -> dict[str, Any]:
        moment = at or datetime.now(UTC)
        scan = scan_id or uuid4()
        manifest: RawArchiveManifest | None = None
        if db is not None:
            manifest = RawArchiveManifest(
                scan_id=scan,
                layer=layer,
                endpoint=endpoint,
                mode=self.mode,
                status="writing",
            )
            db.add(manifest)
            await db.flush()

        if self.mode == "audit":
            name = f"scan-{scan}-{endpoint}"
            latest = self.bundle_path(endpoint, name, moment)
            previous: Path | None = None
        else:
            latest = self.bundle_path(endpoint, "latest", moment)
            previous = self.bundle_path(endpoint, "previous", moment)

        try:
            latest.parent.mkdir(parents=True, exist_ok=True)
            tmp = latest.with_suffix(latest.suffix + ".tmp")
            with tmp.open("wb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
                    if meta:
                        gz.write(_dump_line({"_meta": meta}).encode("utf-8"))
                    for record in records:
                        gz.write(_dump_line(record).encode("utf-8"))
            if previous is not None and latest.exists():
                os.replace(latest, previous)
            os.replace(tmp, latest)
        except Exception as exc:  # noqa: BLE001 - ghi lỗi phải giữ latest cũ
            tmp = latest.with_suffix(latest.suffix + ".tmp")
            tmp.unlink(missing_ok=True)
            if manifest is not None:
                manifest.status = "failed"
                manifest.error = str(exc)[:500]
                await db.flush()
            raise

        size = latest.stat().st_size
        digest = hashlib.sha256(latest.read_bytes()).hexdigest()
        if manifest is not None:
            manifest.status = "success"
            manifest.path_latest = str(latest.relative_to(self.base_dir))
            if previous is not None and previous.exists():
                manifest.path_previous = str(previous.relative_to(self.base_dir))
            manifest.files = 1
            manifest.bytes = size
            manifest.records = len(records)
            manifest.checksum = digest
            manifest.rotated_at = datetime.now(UTC)
            await db.flush()
        return {
            "scan_id": str(scan),
            "endpoint": endpoint,
            "mode": self.mode,
            "path_latest": str(latest),
            "path_previous": str(previous) if previous and previous.exists() else None,
            "files": 1,
            "bytes": size,
            "records": len(records),
            "checksum": digest,
        }

    # ---------- thống kê từ manifest ----------

    async def manifest_stats(self, db: AsyncSession) -> dict[str, Any]:
        rows = (
            await db.execute(
                select(RawArchiveManifest)
                .where(RawArchiveManifest.status == "success")
                .order_by(RawArchiveManifest.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        seen: set[str] = set()
        files = 0
        total_bytes = 0
        records = 0
        latest_at: str | None = None
        for row in reversed(rows):
            files += row.files
            total_bytes += row.bytes
            records += row.records
            seen.add(row.endpoint)
            if latest_at is None or (row.created_at and row.created_at.isoformat() > latest_at):
                latest_at = row.created_at.isoformat() if row.created_at else None
        return {
            "mode": self.mode,
            "files": files,
            "bytes": total_bytes,
            "records": records,
            "endpoints": sorted(seen),
            "latest_at": latest_at,
            "source": "manifest" if rows else "empty",
        }

    # ---------- tương thích cũ ----------

    def path_for(self, endpoint: str, key: str, at: datetime | None = None) -> Path:
        moment = at or datetime.now(UTC)
        return (
            self.base_dir
            / moment.strftime("%Y-%m-%d")
            / moment.strftime("%H")
            / endpoint
            / f"{key}.jsonl"
        )

    def append(
        self,
        endpoint: str,
        key: str,
        records: list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
        at: datetime | None = None,
    ) -> Path | None:
        """Legacy append (giai đoạn chuyển tiếp). Scan mới dùng write_bundle()."""
        if not records:
            return None
        path = self.path_for(endpoint, key, at)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            if meta:
                handle.write(_dump_line({"_meta": meta}))
            for record in records:
                handle.write(_dump_line(record))
        return path

    def stats(self) -> dict[str, int]:
        """Filesystem stats (legacy). API dùng manifest_stats()."""
        if not self.base_dir.exists():
            return {"files": 0, "bytes": 0}
        files = 0
        total = 0
        for path in self.base_dir.rglob("*"):
            if path.is_file():
                files += 1
                total += path.stat().st_size
        return {"files": files, "bytes": total}

    # ---------- retention (dùng ở bước 5.0.3) ----------

    def compress_older_than(self, days: int = 7, now: datetime | None = None) -> dict[str, int]:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
        compressed = 0
        if not self.base_dir.exists():
            return {"compressed": 0}
        for path in self.base_dir.rglob("*.jsonl"):
            if self.mode == "latest_previous" and path.name.startswith("latest"):
                continue
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) >= cutoff:
                continue
            target = path.with_suffix(path.suffix + ".gz")
            with path.open("rb") as source, gzip.open(target, "wb") as sink:
                shutil.copyfileobj(source, sink)
            path.unlink()
            compressed += 1
        return {"compressed": compressed}

    def purge_older_than(self, days: int = 90, now: datetime | None = None) -> dict[str, int]:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
        removed = 0
        if not self.base_dir.exists():
            return {"removed": 0}
        for path in self.base_dir.rglob("*"):
            if not path.is_file() or path.suffix not in {".jsonl", ".gz"}:
                continue
            if self.mode == "latest_previous" and path.name.startswith(("latest", "previous")):
                continue
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
                path.unlink()
                removed += 1
        return {"removed": removed}


async def count_success_manifests(db: AsyncSession) -> int:
    return (
        await db.scalar(
            select(func.count()).select_from(RawArchiveManifest).where(
                RawArchiveManifest.status == "success"
            )
        )
        or 0
    )
