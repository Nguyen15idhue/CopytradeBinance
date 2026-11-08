"""Retention raw archive: audit nén/xoá, latest_previous không xoá."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.raw_manifest import RawArchiveManifest
from app.services.storage.raw import RawArchive
from app.services.storage.retention import run_retention


def _records(count: int = 2) -> list[dict]:
    return [{"leadPortfolioId": f"id-{i}"} for i in range(count)]


@pytest.fixture
def audit_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    settings = get_settings()
    monkeypatch.setattr(settings, "raw_archive_mode", "audit")
    monkeypatch.setattr(settings, "raw_archive_dir", str(tmp_path))
    monkeypatch.setattr(settings, "raw_archive_compress_after_days", 1)
    monkeypatch.setattr(settings, "raw_archive_audit_retention_days", 5)
    return tmp_path


@pytest.mark.asyncio
async def test_latest_previous_never_deletes(audit_mode: Path, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "raw_archive_mode", "latest_previous")
    async with SessionLocal() as db:
        archive = RawArchive(mode="latest_previous")
        await archive.write_bundle(db, "list-public", _records(3))
        await archive.write_bundle(db, "list-public", _records(4))
        await db.commit()
        result = await run_retention(db)
        assert result["removed"] == 0
        files = list((audit_mode / "archive" / "list-public").glob("*.gz"))
        assert {path.name for path in files} == {"latest.jsonl.gz", "previous.jsonl.gz"}


@pytest.mark.asyncio
async def test_audit_dry_run_and_purge(audit_mode: Path) -> None:
    async with SessionLocal() as db:
        before = (
            await db.execute(select(func.coalesce(func.max(RawArchiveManifest.id), 0)))
        ).scalar() or 0
        archive = RawArchive(mode="audit")
        old = await archive.write_bundle(
            db, "list-signal", _records(2), at=datetime.now(UTC) - timedelta(days=10)
        )
        await db.commit()
        old_path = Path(old["path_latest"])
        old_time = (datetime.now(UTC) - timedelta(days=10)).timestamp()
        os.utime(old_path, (old_time, old_time))

        dry = await run_retention(db, dry_run=True)
        assert dry["removed"] == 1
        assert old_path.exists()

        result = await run_retention(db)
        assert result["removed"] == 1
        assert not old_path.exists()
        assert result["purged_manifests"] >= 1

        await db.execute(delete(RawArchiveManifest).where(RawArchiveManifest.id > before))
        await db.commit()
