"""Check the chartItems activity proxy against detail.lastTradeTime.

The list payload has no lastTradeTime, so Phase 0 uses detail to measure how
often `traded_last_7d` (max-min of the last 8 daily chartItems) disagrees with
the real last trade timestamp.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    DATA_DIR,
    RAW_DIR,
    load_json,
    now_ms,
    read_csv,
    read_jsonl,
    save_json,
    write_csv,
)

FIELDS = [
    "portfolio_id",
    "tier",
    "runtime_days",
    "proxy_traded_last_7d",
    "last_trade_time_ms",
    "last_trade_age_days",
    "actual_traded_last_7d",
    "agree",
    "disagreement",
    "chart_items_len",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Activity proxy check")
    parser.add_argument("--universe", default=str(DATA_DIR / "universe_90d.jsonl"))
    parser.add_argument("--manifest", default=str(DATA_DIR / "sample_manifest.csv"))
    args = parser.parse_args()

    universe = {
        str(row.get("leadPortfolioId")): row for row in read_jsonl(args.universe)
    }
    manifest = read_csv(args.manifest)
    current = now_ms()
    rows = []

    for item in manifest:
        pid = str(item.get("portfolio_id"))
        tier = item.get("tier")
        source = universe.get(pid) or {}
        detail_path = RAW_DIR / str(tier) / pid / "detail.json"
        detail_last_trade = None
        if detail_path.exists():
            payload = load_json(detail_path)
            detail = payload.get("data") or {}
            detail_last_trade = detail.get("lastTradeTime")

        proxy = bool(source.get("traded_last_7d"))
        age_days = None
        if detail_last_trade:
            try:
                age_days = (current - int(detail_last_trade)) / 86_400_000.0
            except (TypeError, ValueError):
                age_days = None
        actual = age_days is not None and age_days <= 7.0
        agree = proxy == actual
        if proxy and actual:
            disagreement = ""
        elif proxy and not actual:
            disagreement = "false_positive_proxy_recent_but_old"
        elif not proxy and actual:
            disagreement = "false_negative_proxy_old_but_recent"
        else:
            disagreement = ""

        rows.append(
            {
                "portfolio_id": pid,
                "tier": tier,
                "runtime_days": source.get("runtime_days"),
                "proxy_traded_last_7d": proxy,
                "last_trade_time_ms": detail_last_trade,
                "last_trade_age_days": None if age_days is None else round(age_days, 2),
                "actual_traded_last_7d": actual,
                "agree": agree,
                "disagreement": disagreement,
                "chart_items_len": len(source.get("chartItems") or []),
            }
        )

    write_csv(DATA_DIR / "activity_check.csv", FIELDS, rows)

    total = len(rows)
    agree = sum(1 for r in rows if r["agree"])
    fp = sum(1 for r in rows if r["disagreement"].startswith("false_positive"))
    fn = sum(1 for r in rows if r["disagreement"].startswith("false_negative"))
    summary = {
        "checked": total,
        "agree": agree,
        "agreement_rate": round(agree / total, 4) if total else None,
        "false_positive": fp,
        "false_negative": fn,
        "false_positive_rate": round(fp / total, 4) if total else None,
        "false_negative_rate": round(fn / total, 4) if total else None,
        "by_tier": {},
        "note": (
            "Proxy uses chartItems, which is cumulative ROI and does not change "
            "when a trader only holds positions without new fills."
        ),
    }
    for tier in sorted({str(r["tier"]) for r in rows}):
        subset = [r for r in rows if str(r["tier"]) == tier]
        summary["by_tier"][tier] = {
            "checked": len(subset),
            "agree": sum(1 for r in subset if r["agree"]),
            "false_positive": sum(
                1 for r in subset if r["disagreement"].startswith("false_positive")
            ),
            "false_negative": sum(
                1 for r in subset if r["disagreement"].startswith("false_negative")
            ),
        }
    save_json(DATA_DIR / "activity_check_summary.json", summary)

    print(
        f"[activity] checked={total} agree={agree} ({summary['agreement_rate']:.1%}) "
        f"FP={fp} FN={fn}"
    )
    for tier, stats in summary["by_tier"].items():
        print(f"  {tier:>8}: {stats}")


if __name__ == "__main__":
    main()
