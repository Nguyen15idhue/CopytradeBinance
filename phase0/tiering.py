"""Pre-filter, potential tiers and pre-score.

This module is intentionally pure: no network, no database. It implements the
funnel described in docs/kehoach/02-data-contract-binance.md section 3.1.

Terminology
-----------
* Watch (C)          : passes the cheap list pre-filter.
* Qualified (B)      : Watch + stricter list thresholds. Still an upper bound
                       because totalOrder is only known from /performance.
* High (A)           : Qualified + the strictest list thresholds.
* Excluded           : at least one hard exclusion reason.

B and A are subsets of C. They must never be added together.
"""
from __future__ import annotations

import bisect
import math
from typing import Any, Iterable

PRESETS = {
    "broad": 1_000.0,
    "balanced": 5_000.0,
    "strict": 10_000.0,
}

TIER_LABELS = {
    "excluded": "Excluded",
    "watch": "C — Watch",
    "qualified_upper": "B — Qualified (upper bound)",
    "high_upper": "A — High (upper bound)",
}

# Thresholds (percent values, exactly as the BAPI returns them).
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


def fnum(value: Any) -> float | None:
    """Best-effort float conversion. Empty strings and None stay None."""
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


def traded_last_7d(item: dict) -> bool:
    """Proxy for recent activity using the last 8 daily chartItems.

    chartItems is cumulative ROI, heavily distorted by deposits/withdrawals.
    It is used only as a cheap activity proxy on the list payload, never to
    compute performance metrics.
    """
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


def evaluate_item(item: dict, now_ms: int, aum_min: float = 5_000.0) -> dict:
    """Return tier, reasons and the list-level metrics used by the funnel."""
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
    missing: list[str] = []

    for name, value in (
        ("roi", roi),
        ("pnl", pnl),
        ("winRate", win_rate),
        ("mdd", mdd),
        ("aum", aum),
        ("startTime", fnum(item.get("startTime"))),
    ):
        if value is None:
            missing.append(name)

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
        if _is_qualified_upper(
            runtime=runtime,
            roi=roi,
            win_rate=win_rate,
            mdd=mdd,
            aum=aum,
            sharpe=sharpe,
        ):
            tier = "qualified_upper"
        if _is_high_upper(
            runtime=runtime,
            roi=roi,
            win_rate=win_rate,
            mdd=mdd,
            aum=aum,
            sharpe=sharpe,
        ):
            tier = "high_upper"

    return {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "reasons": reasons,
        "primary_reason": reasons[0] if reasons else "",
        "missing_fields": missing,
        "runtime_days": round(runtime, 2),
        "traded_last_7d": recent,
        "roi": roi,
        "pnl": pnl,
        "win_rate": win_rate,
        "mdd": mdd,
        "aum": aum,
        "copy_aum": fnum(item.get("copyAum")),
        "sharpe": sharpe,
        "current_copy_count": current_copies,
        "max_copy_count": max_copies,
    }


def _is_qualified_upper(
    *,
    runtime: float,
    roi: float | None,
    win_rate: float | None,
    mdd: float | None,
    aum: float | None,
    sharpe: float | None,
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
    if sharpe is not None and sharpe < B_MIN_SHARPE:
        return False
    return True


def _is_high_upper(
    *,
    runtime: float,
    roi: float | None,
    win_rate: float | None,
    mdd: float | None,
    aum: float | None,
    sharpe: float | None,
) -> bool:
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
    if sharpe is None or sharpe < A_MIN_SHARPE:
        return False
    return True


# ------------------------------------------------------------------ pre-score
def _percentile_rank(sorted_values: list[float], value: float | None) -> float:
    if value is None or not sorted_values:
        return 50.0
    n = len(sorted_values)
    if n == 1:
        return 50.0
    left = bisect.bisect_left(sorted_values, value)
    right = bisect.bisect_right(sorted_values, value)
    average_index = (left + right - 1) / 2.0
    return (average_index / (n - 1)) * 100.0


def annotate_pre_score(rows: Iterable[dict], now_ms: int) -> list[dict]:
    """Attach `pre_score` to each row.

    pre_score = 0.30*norm(roi) + 0.30*norm(-mdd) + 0.20*norm(sharpe)
              + 0.10*norm(winRate) + 0.10*norm(min(runtime/180, 1))

    Missing values use neutral 50, never 0. pre_score is only a deep-fetch
    ordering hint; it is not the final quality score.
    """
    rows = list(rows)
    roi_values = sorted(
        v for v in (fnum(r.get("roi")) for r in rows) if v is not None
    )
    mdd_values = sorted(
        -v for v in (fnum(r.get("mdd")) for r in rows) if v is not None
    )
    sharpe_values = sorted(
        v for v in (fnum(r.get("sharpRatio")) for r in rows) if v is not None
    )
    win_values = sorted(
        v for v in (fnum(r.get("winRate")) for r in rows) if v is not None
    )
    runtime_values = sorted(
        min(runtime_days(r.get("startTime"), now_ms) / 180.0, 1.0) for r in rows
    )

    for row in rows:
        runtime_norm = min(runtime_days(row.get("startTime"), now_ms) / 180.0, 1.0)
        mdd = fnum(row.get("mdd"))
        score = (
            0.30 * _percentile_rank(roi_values, fnum(row.get("roi")))
            + 0.30 * _percentile_rank(mdd_values, -mdd if mdd is not None else None)
            + 0.20 * _percentile_rank(sharpe_values, fnum(row.get("sharpRatio")))
            + 0.10 * _percentile_rank(win_values, fnum(row.get("winRate")))
            + 0.10 * _percentile_rank(runtime_values, runtime_norm)
        )
        row["pre_score"] = round(score, 4)
    return rows


def summarize_tiers(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    total = len(rows)
    counts = {"watch": 0, "qualified_upper": 0, "high_upper": 0, "excluded": 0}
    reasons: dict[str, int] = {}
    for row in rows:
        tier = row.get("tier") or row.get("potential_tier") or "excluded"
        counts[tier] = counts.get(tier, 0) + 1
        for reason in row.get("reasons") or []:
            reasons[reason] = reasons.get(reason, 0) + 1
    watch_only = counts["watch"]
    return {
        "total": total,
        "watch": counts["watch"] + counts["qualified_upper"] + counts["high_upper"],
        "watch_only": watch_only,
        "qualified_only": counts["qualified_upper"],
        "qualified_incl_high": counts["qualified_upper"] + counts["high_upper"],
        "high_only": counts["high_upper"],
        # Backward-compatible aliases used by the scripts.
        "qualified_upper": counts["qualified_upper"],
        "high_upper": counts["high_upper"],
        "excluded": counts["excluded"],
        "reasons": reasons,
        "union_deep_fetch": counts["watch"]
        + counts["qualified_upper"]
        + counts["high_upper"],
    }
