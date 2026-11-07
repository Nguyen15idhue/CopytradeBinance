"""L1 — Pre-filter thuần (không DB): traded_last_7d, tier, reason, pre_score."""

import bisect
import math
from typing import Any

MIN_RUNTIME_DAYS = 30
MIN_ROI_WATCH = 0.0
MIN_PNL_WATCH = 0.0
MIN_WIN_RATE_WATCH = 40.0
MAX_MDD_WATCH = 40.0

B_MIN_RUNTIME_DAYS = 90
B_MIN_ROI = 10.0
B_MIN_WIN_RATE = 45.0
B_MAX_MDD = 30.0
B_MIN_AUM = 10_000.0
B_MIN_SHARPE = 0.5

A_MIN_RUNTIME_DAYS = 180
A_MIN_ROI = 20.0
A_MIN_WIN_RATE = 50.0
A_MAX_MDD = 20.0
A_MIN_AUM = 20_000.0
A_MIN_SHARPE = 1.0

TIER_RANK = {
    "high_upper": 0,
    "qualified_upper": 1,
    "watch": 2,
    "excluded": 9,
}

TIER_LABELS = {
    "excluded": "Excluded",
    "watch": "C — Watch",
    "qualified_upper": "B — Qualified (upper bound)",
    "high_upper": "A — High (upper bound)",
}

# HF04: không đủ mẫu totalOrder thì hạ tier tương ứng.
DEMOTE_RULES = {
    "high_upper": ("qualified_upper", 100),
    "qualified_upper": ("watch", 50),
}


def apply_total_order_demotion(tier: str, total_orders: int | None) -> str:
    rule = DEMOTE_RULES.get(tier)
    if rule is None or total_orders is None:
        return tier
    new_tier, threshold = rule
    return new_tier if total_orders < threshold else tier


def fnum(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def runtime_days(start_time_ms: Any, now_ms: int) -> float:
    start = fnum(start_time_ms)
    if not start or start <= 0:
        return 0.0
    return max(0.0, (now_ms - start) / 86_400_000.0)


def traded_last_7d(item: dict[str, Any]) -> bool:
    """Proxy rẻ từ 8 điểm chartItems cuối; chỉ dùng cho list, không dùng tính metric."""
    chart = item.get("chartItems") or []
    values: list[float] = []
    for point in chart:
        if isinstance(point, dict):
            value = fnum(point.get("value"))
            if value is not None:
                values.append(value)
    if len(values) < 2:
        return False
    window = values[-8:] if len(values) >= 8 else values
    return (max(window) - min(window)) > 1e-9


def _qualified_upper(
    *, runtime: float, roi, win_rate, mdd, aum, sharpe
) -> bool:
    if runtime < B_MIN_RUNTIME_DAYS:
        return False
    if roi is None or roi < B_MIN_ROI:
        return False
    if win_rate is None or win_rate < B_MIN_WIN_RATE:
        return False
    if mdd is None or mdd > B_MAX_MDD:
        return False
    if aum is None or aum < B_MIN_AUM:
        return False
    return not (sharpe is not None and sharpe < B_MIN_SHARPE)


def _high_upper(*, runtime: float, roi, win_rate, mdd, aum, sharpe) -> bool:
    if runtime < A_MIN_RUNTIME_DAYS:
        return False
    if roi is None or roi < A_MIN_ROI:
        return False
    if win_rate is None or win_rate < A_MIN_WIN_RATE:
        return False
    if mdd is None or mdd > A_MAX_MDD:
        return False
    if aum is None or aum < A_MIN_AUM:
        return False
    return sharpe is not None and sharpe >= A_MIN_SHARPE


def evaluate_item(item: dict[str, Any], now_ms: int, aum_min: float = 5_000.0) -> dict[str, Any]:
    roi = fnum(item.get("roi"))
    pnl = fnum(item.get("pnl"))
    win_rate = fnum(item.get("winRate"))
    mdd = fnum(item.get("mdd"))
    aum = fnum(item.get("aum"))
    sharpe = fnum(item.get("sharpRatio"))
    current_copies = fnum(item.get("currentCopyCount")) or 0.0
    max_copies = fnum(item.get("maxCopyCount")) or 0.0
    runtime = runtime_days(item.get("startTime"), now_ms)
    recent = traded_last_7d(item)

    reasons: list[str] = []
    if not recent:
        reasons.append("no_trade_7d")
    if runtime < MIN_RUNTIME_DAYS:
        reasons.append("runtime_lt_30")
    if roi is None or roi <= MIN_ROI_WATCH:
        reasons.append("roi_le_0")
    if pnl is None or pnl <= MIN_PNL_WATCH:
        reasons.append("pnl_le_0")
    if win_rate is None or win_rate < MIN_WIN_RATE_WATCH:
        reasons.append("winrate_lt_40")
    if mdd is not None and mdd > MAX_MDD_WATCH:
        reasons.append("mdd_gt_40")
    if aum is None or aum < aum_min:
        reasons.append("aum_lt_5000" if aum_min == 5_000 else f"aum_lt_{int(aum_min)}")
    if max_copies <= 0 or current_copies >= max_copies:
        reasons.append("no_slots")

    tier = "excluded"
    if not reasons:
        tier = "watch"
        if _qualified_upper(
            runtime=runtime, roi=roi, win_rate=win_rate, mdd=mdd, aum=aum, sharpe=sharpe
        ):
            tier = "qualified_upper"
        if _high_upper(
            runtime=runtime, roi=roi, win_rate=win_rate, mdd=mdd, aum=aum, sharpe=sharpe
        ):
            tier = "high_upper"

    return {
        "tier": tier,
        "reasons": reasons,
        "primary_reason": reasons[0] if reasons else "",
        "runtime_days": round(runtime, 2),
        "traded_last_7d": recent,
        "roi": roi,
        "mdd": mdd,
        "sharpe": sharpe,
        "win_rate": win_rate,
        "aum": aum,
    }


def percentile_rank(sorted_values: list[float], value: float | None) -> float:
    if value is None or not sorted_values:
        return 50.0
    count = len(sorted_values)
    if count == 1:
        return 50.0
    left = bisect.bisect_left(sorted_values, value)
    right = bisect.bisect_right(sorted_values, value)
    average_index = (left + right - 1) / 2.0
    return (average_index / (count - 1)) * 100.0


def annotate_pre_score(rows: list[dict[str, Any]], now_ms: int) -> list[dict[str, Any]]:
    """pre_score percentile trên một cohort chung (quyết định Q02)."""
    roi_values = sorted(v for v in (fnum(row.get("roi")) for row in rows) if v is not None)
    mdd_values = sorted(
        -v for v in (fnum(row.get("mdd")) for row in rows) if v is not None
    )
    sharpe_values = sorted(
        v for v in (fnum(row.get("sharpRatio")) for row in rows) if v is not None
    )
    win_values = sorted(
        v for v in (fnum(row.get("winRate")) for row in rows) if v is not None
    )
    runtime_values = sorted(
        min(runtime_days(row.get("startTime"), now_ms) / 180.0, 1.0) for row in rows
    )

    for row in rows:
        mdd = fnum(row.get("mdd"))
        runtime_norm = min(runtime_days(row.get("startTime"), now_ms) / 180.0, 1.0)
        row["pre_score"] = round(
            0.30 * percentile_rank(roi_values, fnum(row.get("roi")))
            + 0.30 * percentile_rank(mdd_values, -mdd if mdd is not None else None)
            + 0.20 * percentile_rank(sharpe_values, fnum(row.get("sharpRatio")))
            + 0.10 * percentile_rank(win_values, fnum(row.get("winRate")))
            + 0.10 * percentile_rank(runtime_values, runtime_norm),
            4,
        )
    return rows
