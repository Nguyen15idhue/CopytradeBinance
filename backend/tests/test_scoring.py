import pytest

from app.services.scoring import (
    COMPONENTS,
    band_for,
    compute_scores,
    hard_flags,
    normalize_cohort,
    percentile_rank,
    pnl_per_aum,
    pnl_scale,
)


def _row(pid, **components):
    return {"id": pid, "components": components}


def test_percentile_rank_range() -> None:
    values = [1, 2, 3, 4, 5]
    assert percentile_rank(values, 1) == 0
    assert percentile_rank(values, 5) == 100
    assert 0 < percentile_rank(values, 3) < 100


def test_normalize_reverses_lower_is_better() -> None:
    raw = {"mdd": [10.0, 20.0], "roi_90d": [5.0, 15.0]}
    normalized = normalize_cohort(raw)
    assert normalized["0"]["mdd"] > normalized["1"]["mdd"]  # MDD thấp tốt hơn
    assert normalized["0"]["roi_90d"] < normalized["1"]["roi_90d"]


def test_missing_component_is_dropped_and_renormalized() -> None:
    rows = [
        _row("a", mdd=10.0, roi_90d=5.0),
        _row("b", mdd=20.0, roi_90d=15.0),
    ]
    results = {item["id"]: item for item in compute_scores(rows)}
    assert set(results["a"]["components"]) == {"risk_management", "profitability"}
    assert results["a"]["score"] is not None
    assert 0 <= results["a"]["score"] <= 100
    assert len(results["a"]["missing"]) == len(COMPONENTS) - 2


def test_breakdown_contributions_sum_to_score() -> None:
    rows = [
        _row(
            "a",
            mdd=10,
            calmar=2,
            roi_90d=20,
            profit_factor=2,
            confidence=0.9,
            sample_size=100,
        ),
        _row(
            "b",
            mdd=30,
            calmar=0.5,
            roi_90d=5,
            profit_factor=1.1,
            confidence=0.6,
            sample_size=50,
        ),
    ]
    results = compute_scores(rows)
    for result in results:
        total = sum(item["contribution"] for item in result["components"].values())
        assert total == pytest.approx(result["score"], abs=0.01)


def test_overall_score_not_driven_by_roi_only() -> None:
    rows = [
        _row("risky", roi_90d=100, mdd=40, max_leverage=25, worst_position_roi=-95),
        _row("safe", roi_90d=20, mdd=8, max_leverage=3, worst_position_roi=-20),
    ]
    results = {item["id"]: item for item in compute_scores(rows)}
    assert results["safe"]["score"] > results["risky"]["score"]


def test_band_boundaries() -> None:
    assert band_for(85) == "excellent"
    assert band_for(84.99) == "good"
    assert band_for(70) == "good"
    assert band_for(55) == "average"
    assert band_for(40) == "weak"
    assert band_for(39.9) == "high_risk"
    assert band_for(None) is None


def test_hard_flags_tier_thresholds() -> None:
    base = {
        "status": "ACTIVE",
        "runtime_days": 200,
        "freshness_minutes": 10,
        "confidence": 0.9,
    }
    assert hard_flags(tier="watch", total_orders=20, **base) == []
    assert "hf04_low_orders" in hard_flags(tier="watch", total_orders=19, **base)
    assert hard_flags(tier="qualified_upper", total_orders=50, **base) == []
    assert "hf04_low_orders" in hard_flags(tier="qualified_upper", total_orders=49, **base)
    assert hard_flags(tier="high_upper", total_orders=100, **base) == []
    assert "hf04_low_orders" in hard_flags(tier="high_upper", total_orders=99, **base)


def test_hard_flags_status_and_confidence() -> None:
    flags = hard_flags(
        status="PAUSED",
        tier="excluded",
        runtime_days=10,
        total_orders=5,
        freshness_minutes=200,
        confidence=0.3,
    )
    assert {
        "hf01_not_active",
        "hf02_excluded",
        "hf03_runtime_lt_30",
        "hf04_low_orders",
        "hf05_stale",
        "hf06_low_confidence",
    } <= set(flags)


def test_capital_efficiency_helpers() -> None:
    assert pnl_per_aum(100, 1000) == 10
    assert pnl_per_aum(100, 0) is None
    assert pnl_scale(None) is None
    assert pnl_scale(-5) == 0
    assert pnl_scale(999) == pytest.approx(3.0)
