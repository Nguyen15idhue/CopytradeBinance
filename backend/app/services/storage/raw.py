"""Ghi raw JSONL append-only + nén/retention."""

import gzip
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class RawArchive:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or get_settings().raw_archive_dir)

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
        if not records:
            return None
        path = self.path_for(endpoint, key, at)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            if meta:
                handle.write(json.dumps({"_meta": meta}, ensure_ascii=False) + "\n")
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return path

    def stats(self) -> dict[str, int]:
        if not self.base_dir.exists():
            return {"files": 0, "bytes": 0}
        files = 0
        total = 0
        for path in self.base_dir.rglob("*"):
            if path.is_file():
                files += 1
                total += path.stat().st_size
        return {"files": files, "bytes": total}

    def compress_older_than(self, days: int = 7, now: datetime | None = None) -> dict[str, int]:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
        compressed = 0
        if not self.base_dir.exists():
            return {"compressed": 0}
        for path in self.base_dir.rglob("*.jsonl"):
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
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
                path.unlink()
                removed += 1
        return {"removed": removed}
