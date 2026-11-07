from datetime import UTC, datetime, timedelta

from app.worker.scheduler import due_jobs

INTERVALS = {
    "scan": timedelta(minutes=60),
    "perf": timedelta(hours=6),
    "detail": timedelta(hours=12),
    "trades": timedelta(hours=24),
}
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def test_due_jobs_respects_intervals() -> None:
    last_run = {
        "scan": NOW - timedelta(minutes=59),
        "perf": NOW - timedelta(hours=7),
        "detail": NOW - timedelta(hours=3),
        "trades": NOW - timedelta(hours=25),
    }
    assert due_jobs(NOW, last_run, INTERVALS) == ["perf", "trades"]


def test_due_jobs_runs_when_never_run() -> None:
    assert due_jobs(NOW, {}, INTERVALS) == ["scan", "perf", "detail", "trades"]


def test_due_jobs_exact_boundary() -> None:
    last_run = {"scan": NOW - timedelta(minutes=60)}
    assert "scan" in due_jobs(NOW, last_run, INTERVALS)
