"""Phân mức độ mới của dữ liệu (kế hoạch 05, bước 5.0.8)."""

from typing import Any

STALE_MINUTES = 150
VERY_STALE_MINUTES = 1440


def level(minutes: float | None) -> str:
    if minutes is None:
        return "unknown"
    if minutes <= STALE_MINUTES:
        return "ok"
    if minutes <= VERY_STALE_MINUTES:
        return "stale"
    return "very_stale"


def payload(minutes: float | None, as_of: str | None = None) -> dict[str, Any]:
    rounded = round(float(minutes), 2) if minutes is not None else None
    return {
        "minutes": rounded,
        "level": level(rounded),
        "as_of": as_of,
        "stale_minutes": STALE_MINUTES,
        "very_stale_minutes": VERY_STALE_MINUTES,
    }


def from_metrics(metrics: dict[str, Any] | None) -> dict[str, Any]:
    blob = metrics or {}
    provenance = blob.get("provenance") or {}
    as_of = provenance.get("performance_at")
    minutes = blob.get("freshness_minutes")
    try:
        value = float(minutes) if minutes is not None else None
    except (TypeError, ValueError):
        value = None
    return payload(value, as_of)
