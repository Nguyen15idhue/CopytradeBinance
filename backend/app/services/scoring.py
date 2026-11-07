"""Scoring v1.0: percentile trong cohort, winsorize, renormalize missing."""

import math
from typing import Any

WINSOR_LOW = 2.5
WINSOR_HIGH = 97.5

GROUP_WEIGHTS = {
    "risk_management": 25,
    "consistency": 20,
    "profitability": 15,
    "trading_quality": 15,
    "copy_performance": 10,
    "capital_efficiency": 5,
    "data_reliability": 10,
}

# name: (group, weight within group, direction, label)
COMPONENTS: dict[str, tuple[str, float, str, str]] = {
    "mdd": ("risk_management", 10, "lower", "MDD 90D"),
    "calmar": ("risk_management", 5, "higher", "Calmar"),
    "max_leverage": ("risk_management", 5, "lower", "Max leverage"),
    "worst_position_roi": ("risk_management", 5, "higher", "Worst position ROI"),
    "positive_days_pct": ("consistency", 8, "higher", "Positive days"),
    "roi_stability": ("consistency", 6, "lower", "ROI stability"),
    "roi_90d": ("profitability", 8, "higher", "ROI 90D"),
    "excess_return": ("profitability", 4, "higher", "Excess return"),
    "pnl_scale": ("profitability", 3, "higher", "PnL scale"),
    "profit_factor": ("trading_quality", 6, "higher", "Profit factor"),
    "payoff_ratio": ("trading_quality", 4, "higher", "Payoff ratio"),
    "win_rate_order_90d": ("trading_quality", 5, "higher", "WinRate order"),
    "copier_pnl_90d": ("copy_performance", 4, "higher", "Copier PnL"),
    "copy_aum_ratio": ("copy_performance", 3, "higher", "Copy AUM ratio"),
    "current_copiers": ("copy_performance", 3, "higher", "Copiers"),
    "pnl_per_aum": ("capital_efficiency", 3, "higher", "PnL/AUM"),
    "aum": ("capital_efficiency", 2, "higher", "AUM"),
    "confidence": ("data_reliability", 6, "higher", "Confidence"),
    "sample_size": ("data_reliability", 4, "higher", "Sample size"),
}

BANDS = (
    (85, "excellent"),
    (70, "good"),
    (55, "average"),
    (40, "weak"),
    (0, "high_risk"),
)


def percentile_rank(sorted_values: list[float], value: float) -> float:
    import bisect

    if not sorted_values:
        return 50.0
    if len(sorted_values) == 1:
        return 50.0
    left = bisect.bisect_left(sorted_values, value)
    right = bisect.bisect_right(sorted_values, value)
    return ((left + right - 1) / 2.0) / (len(sorted_values) - 1) * 100


def _bounds(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    ordered = sorted(values)
    low = ordered[max(0, int(len(ordered) * WINSOR_LOW / 100) - 1)]
    high = ordered[min(len(ordered) - 1, int(len(ordered) * WINSOR_HIGH / 100))]
    return low, high


def normalize_cohort(raw: dict[str, list[float | None]]) -> dict[str, dict[str, float]]:
    """Chuẩn hóa từng component theo cohort; trả map id→component→0..100."""
    normalized: dict[str, dict[str, float]] = {}
    for name, values in raw.items():
        present = sorted(value for value in values if value is not None)
        low, high = _bounds(present)
        for index, value in enumerate(values):
            if value is None:
                continue
            clipped = min(max(value, low), high)
            score = percentile_rank(present, clipped)
            if COMPONENTS[name][2] == "lower":
                score = 100 - score
            normalized.setdefault(str(index), {})[name] = round(score, 4)
    return normalized


def compute_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """rows: [{'id': str, 'components': {name: raw|null}}]. Trả score + breakdown."""
    raw: dict[str, list[float | None]] = {name: [] for name in COMPONENTS}
    for row in rows:
        for name in COMPONENTS:
            raw[name].append(row["components"].get(name))
    normalized = normalize_cohort(raw)

    results: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        components = normalized.get(str(index), {})
        groups: dict[str, dict[str, Any]] = {}
        for group in GROUP_WEIGHTS:
            members = [
                (name, weight)
                for name, (group_name, weight, _direction, _label) in COMPONENTS.items()
                if group_name == group and name in components
            ]
            if not members:
                continue
            total_member_weight = sum(weight for _name, weight in members)
            group_score = sum(components[name] * weight for name, weight in members) / (
                total_member_weight or 1
            )
            groups[group] = {
                "score": round(group_score, 4),
                "weight": GROUP_WEIGHTS[group],
                "missing": [
                    name
                    for name, (group_name, _w, _d, _l) in COMPONENTS.items()
                    if group_name == group and name not in components
                ],
            }

        total_weight = sum(item["weight"] for item in groups.values())
        if total_weight == 0:
            score = None
        else:
            score = sum(item["score"] * item["weight"] for item in groups.values()) / total_weight
        for item in groups.values():
            item["contribution"] = (
                round(item["score"] * item["weight"] / total_weight, 4) if total_weight else None
            )
        missing = [
            name
            for name in COMPONENTS
            if name not in components
        ]
        results.append(
            {
                "id": row["id"],
                "score": round(score, 4) if score is not None else None,
                "band": band_for(score),
                "components": groups,
                "missing": missing,
            }
        )
    return results


def band_for(score: float | None) -> str | None:
    if score is None:
        return None
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "high_risk"


def pnl_per_aum(pnl: float | None, aum: float | None) -> float | None:
    if pnl is None or not aum:
        return None
    return pnl / aum * 100


def pnl_scale(pnl: float | None) -> float | None:
    if pnl is None:
        return None
    return round(math.log10(1 + max(pnl, 0.0)), 6)


def hard_flags(
    *,
    status: str | None,
    tier: str,
    runtime_days: float | None,
    total_orders: int | None,
    freshness_minutes: float | None,
    confidence: float | None,
) -> list[str]:
    flags: list[str] = []
    if status != "ACTIVE":
        flags.append("hf01_not_active")
    if tier == "excluded":
        flags.append("hf02_excluded")
    if runtime_days is None or runtime_days < 30:
        flags.append("hf03_runtime_lt_30")
    minimum_orders = {"high_upper": 100, "qualified_upper": 50}.get(tier, 20)
    if (total_orders or 0) < minimum_orders:
        flags.append("hf04_low_orders")
    if freshness_minutes is None or freshness_minutes > 150:
        flags.append("hf05_stale")
    if confidence is None or confidence < 0.5:
        flags.append("hf06_low_confidence")
    return flags
