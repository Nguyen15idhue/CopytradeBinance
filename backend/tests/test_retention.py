import os
from datetime import UTC, datetime, timedelta

from app.services.storage.raw import RawArchive


def _touch(path, age_days: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    stamp = (datetime.now(UTC) - timedelta(days=age_days)).timestamp()
    os.utime(path, (stamp, stamp))


def test_compress_then_purge(tmp_path) -> None:
    archive = RawArchive(str(tmp_path))
    old = tmp_path / "2026-01-01" / "00" / "list" / "p1.jsonl"
    new = tmp_path / "2026-02-01" / "00" / "list" / "p2.jsonl"
    _touch(old, 10)
    _touch(new, 1)

    assert archive.compress_older_than(days=7)["compressed"] == 1
    assert not old.exists()
    assert old.with_suffix(".jsonl.gz").exists()
    assert new.exists()

    assert archive.stats()["files"] == 2
    assert archive.purge_older_than(days=90)["removed"] == 0


def test_purge_removes_expired(tmp_path) -> None:
    archive = RawArchive(str(tmp_path))
    expired = tmp_path / "2025-01-01" / "00" / "list" / "p1.jsonl.gz"
    expired.parent.mkdir(parents=True, exist_ok=True)
    expired.write_text("x", encoding="utf-8")
    stamp = (datetime.now(UTC) - timedelta(days=120)).timestamp()
    os.utime(expired, (stamp, stamp))

    assert archive.purge_older_than(days=90)["removed"] == 1
    assert not expired.exists()
