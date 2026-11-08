import gzip
import json
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.raw_manifest import RawArchiveManifest
from app.services.storage.raw import RawArchive


@pytest.fixture(autouse=True)
async def _clean_manifest_rows():
    """Chỉ xoá manifest do test này tạo, không đụng dữ liệu thật."""
    async with SessionLocal() as db:
        before = (
            await db.execute(select(func.coalesce(func.max(RawArchiveManifest.id), 0)))
        ).scalar() or 0
    yield
    async with SessionLocal() as db:
        await db.execute(
            delete(RawArchiveManifest).where(RawArchiveManifest.id > before)
        )
        await db.commit()


def _records(count: int = 3) -> list[dict]:
    return [{"leadPortfolioId": f"id-{i}", "roi": i + 0.5} for i in range(count)]


def _read_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


@pytest.mark.asyncio
async def test_two_scans_same_hour_only_latest_previous(tmp_path: Path) -> None:
    async with SessionLocal() as db:
        archive = RawArchive(base_dir=str(tmp_path), mode="latest_previous")
        first = await archive.write_bundle(db, "list-public", _records(3))
        second = await archive.write_bundle(db, "list-public", _records(5))
        await db.commit()

        endpoint_dir = tmp_path / "archive" / "list-public"
        names = sorted(path.name for path in endpoint_dir.iterdir())
        assert names == ["latest.jsonl.gz", "previous.jsonl.gz"]
        assert first["records"] == 3
        assert second["records"] == 5
        latest = _read_jsonl(endpoint_dir / "latest.jsonl.gz")
        previous = _read_jsonl(endpoint_dir / "previous.jsonl.gz")
        assert len(latest) == 5
        assert len(previous) == 3
        assert latest[0]["leadPortfolioId"] == "id-0"


@pytest.mark.asyncio
async def test_failed_write_keeps_latest_and_cleans_tmp(tmp_path: Path) -> None:
    async with SessionLocal() as db:
        archive = RawArchive(base_dir=str(tmp_path), mode="latest_previous")
        await archive.write_bundle(db, "list-public", _records(2))
        await db.commit()
        endpoint_dir = tmp_path / "archive" / "list-public"
        before = (endpoint_dir / "latest.jsonl.gz").read_bytes()

        class Boom:
            def __str__(self) -> str:
                raise RuntimeError("boom")

        with pytest.raises((RuntimeError, TypeError, ValueError)):
            await archive.write_bundle(
                db, "list-public", [{"bad": Boom()}]
            )
        await db.rollback()

        assert (endpoint_dir / "latest.jsonl.gz").read_bytes() == before
        assert not list(endpoint_dir.glob("*.tmp"))


@pytest.mark.asyncio
async def test_manifest_stats_does_not_scan_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with SessionLocal() as db:
        archive = RawArchive(base_dir=str(tmp_path), mode="latest_previous")
        await archive.write_bundle(db, "list-public", _records(4))
        await db.commit()

        def boom(*args, **kwargs):
            raise AssertionError("manifest_stats không được quét filesystem")

        monkeypatch.setattr(Path, "rglob", boom)
        stats = await archive.manifest_stats(db)
        assert stats["source"] == "manifest"
        assert stats["files"] >= 1
        assert stats["records"] >= 4
        assert stats["bytes"] > 0
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_audit_mode_writes_dated_bundle(tmp_path: Path) -> None:
    async with SessionLocal() as db:
        archive = RawArchive(base_dir=str(tmp_path), mode="audit")
        info = await archive.write_bundle(db, "list-signal", _records(2))
        await db.commit()
        path = Path(info["path_latest"])
        assert path.exists()
        assert path.parent.name == tmp_path.joinpath().name or path.parent.parent.name == "archive"
        assert info["path_previous"] is None
        assert len(_read_jsonl(path)) == 2
