"""Data confidence theo §8.8."""

from typing import Any

REQUIRED_FIELDS = (
    "roi",
    "pnl",
    "mdd",
    "sharpe",
    "win_rate",
    "total_orders",
    "aum",
    "copy_aum",
    "current_copiers",
    "runtime_days",
    "max_leverage",
    "position_win_rate",
)


def coverage(fields: dict[str, Any]) -> float:
    present = sum(1 for name in REQUIRED_FIELDS if fields.get(name) is not None)
    return present / len(REQUIRED_FIELDS)


def history_score(runtime_days: float | None) -> float:
    if runtime_days is None:
        return 0.0
    return min(max(runtime_days, 0.0) / 90.0, 1.0)


def freshness_score(freshness_minutes: float | None) -> float:
    if freshness_minutes is None:
        return 0.0
    if freshness_minutes <= 60:
        return 1.0
    if freshness_minutes >= 24 * 60:
        return 0.0
    return 1.0 - (freshness_minutes - 60) / (24 * 60 - 60)


def continuity_score(days_with_snapshot: int, expected_days: int = 7) -> float:
    return min(days_with_snapshot / expected_days, 1.0)


def label_for(value: float) -> str:
    if value >= 0.80:
        return "high"
    if value >= 0.60:
        return "medium"
    if value >= 0.40:
        return "low"
    return "insufficient"


def compute_confidence(
    fields: dict[str, Any],
    runtime_days: float | None,
    freshness_minutes: float | None,
    days_with_snapshot: int,
) -> dict[str, Any]:
    parts = {
        "coverage": round(coverage(fields), 4),
        "history": round(history_score(runtime_days), 4),
        "freshness": round(freshness_score(freshness_minutes), 4),
        "continuity": round(continuity_score(days_with_snapshot), 4),
    }
    value = round(
        0.40 * parts["coverage"]
        + 0.30 * parts["history"]
        + 0.20 * parts["freshness"]
        + 0.10 * parts["continuity"],
        4,
    )
    return {"value": value, "label": label_for(value), "parts": parts}
