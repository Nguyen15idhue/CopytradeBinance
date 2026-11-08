"""Scheduler dựa trên last_success từ collection_logs (kế hoạch 05, bước 5.0.5)."""

from datetime import UTC, datetime, timedelta

from app.worker.scheduler import due_jobs, jitter_for, next_due

INTERVALS = {
    "scan": timedelta(hours=1),
    "perf": timedelta(hours=6),
    "detail": timedelta(hours=12),
    "trades": timedelta(hours=24),
    "retention": timedelta(days=1),
}


def test_no_last_success_is_due_immediately() -> None:
    now = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    due = due_jobs(now, {"perf": None}, INTERVALS)
    assert "perf" in due


def test_recent_success_not_due() -> None:
    now = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=10)
    due = due_jobs(now, {"scan": last}, INTERVALS)
    assert "scan" not in due


def test_restart_does_not_reset_clock() -> None:
    """perf mới chạy 5h45 trước → chưa đến hạn dù process vừa start."""
    now = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    last = now - timedelta(hours=5, minutes=45)
    assert "perf" not in due_jobs(now, {"perf": last}, INTERVALS)

    old = now - timedelta(hours=6, minutes=10)
    assert "perf" in due_jobs(now, {"perf": old}, INTERVALS)


def test_overdue_job_runs_on_startup() -> None:
    now = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    last = now - timedelta(days=2)
    due = due_jobs(now, {"detail": last, "trades": last}, INTERVALS)
    assert {"detail", "trades"} <= set(due)


def test_retry_at_overrides_interval() -> None:
    now = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=5)
    retry_at = {"perf": now + timedelta(minutes=10)}
    assert "perf" not in due_jobs(now, {"perf": last}, INTERVALS, retry_at)

    retry_due = {"perf": now - timedelta(seconds=1)}
    assert "perf" in due_jobs(now, {"perf": last}, INTERVALS, retry_due)


def test_jitter_is_stable_and_bounded() -> None:
    first = jitter_for("perf")
    second = jitter_for("perf")
    assert first == second
    assert abs(first.total_seconds()) <= 5 * 60


def test_next_due_includes_jitter() -> None:
    last = datetime(2026, 11, 8, 6, 0, tzinfo=UTC)
    due = next_due("perf", last, timedelta(hours=6))
    base = last + timedelta(hours=6)
    assert due - base == jitter_for("perf")
