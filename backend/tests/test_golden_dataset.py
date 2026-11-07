import json
from pathlib import Path

import pytest

from app.services.scoring import compute_scores, hard_flags

FIXTURE = Path(__file__).parent / "fixtures" / "golden_traders.json"


def _golden():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_golden_fixture_has_12_archetypes_with_two_excluded() -> None:
    rows = _golden()
    assert len(rows) == 12
    assert sum(1 for row in rows if row["expected"] == "excluded") == 2


def test_golden_top_never_contains_excluded_archetypes() -> None:
    rows = _golden()
    results = compute_scores([{"id": row["id"], "components": row["components"]} for row in rows])
    ranked = sorted(results, key=lambda item: item["score"], reverse=True)
    top5 = {item["id"] for item in ranked[:5]}
    assert "golden-excluded-new" not in top5
    assert "golden-excluded-blowup" not in top5


def test_golden_breakdown_matches_score() -> None:
    rows = _golden()
    results = compute_scores([{"id": row["id"], "components": row["components"]} for row in rows])
    for result in results:
        total = sum(item["contribution"] for item in result["components"].values())
        assert total == pytest.approx(result["score"], abs=0.01)


def test_missing_components_are_not_zero() -> None:
    rows = _golden()
    results = {
        item["id"]: item
        for item in compute_scores(
            [{"id": row["id"], "components": row["components"]} for row in rows]
        )
    }
    excluded = results["golden-excluded-new"]
    assert "calmar" in excluded["missing"]
    assert excluded["score"] is not None
    assert excluded["score"] != 0


def test_excluded_archetypes_fail_hard_filters() -> None:
    rows = {row["id"]: row for row in _golden()}
    for pid in ("golden-excluded-new", "golden-excluded-blowup"):
        row = rows[pid]
        flags = hard_flags(
            status="ACTIVE",
            tier="high_upper",
            runtime_days=row["components"].get("sample_size", 0),
            total_orders=row["components"].get("sample_size", 0),
            freshness_minutes=10,
            confidence=row["components"].get("confidence", 0),
        )
        assert "hf04_low_orders" in flags or "hf06_low_confidence" in flags
