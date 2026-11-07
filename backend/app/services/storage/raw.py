"""Ghi raw JSONL append-only: data/raw/{YYYY-MM-DD}/{HH}/{endpoint}/{key}.jsonl."""

import json
from datetime import UTC, datetime
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
