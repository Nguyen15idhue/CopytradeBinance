from datetime import UTC, datetime

from app.services.funnel_audit import watch_eligible

NOW = datetime(2026, 11, 7, tzinfo=UTC)


def _detail(**overrides):
    base = {
        "status": "ACTIVE",
        "isPaused": False,
        "startTime": int((NOW.timestamp() - 100 * 86_400) * 1000),
        "aumAmount": "30000",
        "currentCopyCount": 10,
        "maxCopyCount": 200,
        "lastTradeTime": int((NOW.timestamp() - 3600) * 1000),
    }
    base.update(overrides)
    return base


def _perf(**overrides):
    base = {
        "roi": 12.0,
        "pnl": 100.0,
        "winRate": 50.0,
        "mdd": 20.0,
        "totalOrder": 40,
    }
    base.update(overrides)
    return base


def test_watch_eligible_passes_all_conditions() -> None:
    result = watch_eligible(_detail(), _perf(), NOW)
    assert result["eligible"] is True
    assert result["reasons"] == []


def test_watch_eligible_flags_each_failure() -> None:
    result = watch_eligible(
        _detail(status="PAUSED", isPaused=True, aumAmount="100", currentCopyCount=200),
        _perf(roi=-1, pnl=0, winRate=20, mdd=55, totalOrder=5),
        NOW,
    )
    assert result["eligible"] is False
    assert {
        "not_active",
        "paused",
        "roi_le_0",
        "pnl_le_0",
        "winrate_lt_40",
        "mdd_gt_40",
        "aum_lt_5000",
        "total_orders_lt_20",
        "no_slots",
    } <= set(result["reasons"])


def test_missing_performance_is_not_eligible() -> None:
    result = watch_eligible(_detail(), {}, NOW)
    assert result["eligible"] is False
    assert "roi_le_0" in result["reasons"]
