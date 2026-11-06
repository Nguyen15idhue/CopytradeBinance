"""Recompute tier_summary.csv from an existing universe JSONL (no network)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import DATA_DIR, iso_now, load_json, read_jsonl, save_json, write_csv
from tiering import summarize_tiers

FIXED_REASONS = [
    "runtime_lt_30",
    "no_trade_7d",
    "roi_le_0",
    "pnl_le_0",
    "winrate_lt_40",
    "mdd_gt_40",
    "aum_lt_1000",
    "aum_lt_5000",
    "aum_lt_10000",
    "no_slots",
]


def build_rows(rows: list[dict], scan_summary: dict) -> list[dict]:
    sources: dict[str, list[dict]] = {}
    for row in rows:
        for source in str(row.get("source_portfolio_type") or "UNKNOWN").split(","):
            sources.setdefault(source.strip(), []).append(row)

    reason_keys = set(FIXED_REASONS)
    stats_by_scope = {scope: summarize_tiers(items) for scope, items in sources.items()}
    combined = summarize_tiers(rows)
    stats_by_scope["TOTAL"] = combined
    for stats in stats_by_scope.values():
        reason_keys.update(stats["reasons"].keys())
    reason_keys = [r for r in FIXED_REASONS if r in reason_keys] + sorted(
        reason_keys - set(FIXED_REASONS)
    )

    per_type_meta = scan_summary.get("per_type", {})
    summary_rows = []
    for scope, stats in stats_by_scope.items():
        meta = per_type_meta.get(scope, {})
        as_total = sum(len(v) for v in sources.values())
        row = {
            "scope": scope,
            "total_reported": meta.get("reported_total", stats["total"]),
            "fetched_unique": stats["total"],
            "coverage_pct": round(
                (meta.get("coverage", 1.0) if scope != "TOTAL" else (len(rows) / as_total if as_total else 1.0))
                * 100,
                4,
            ),
            "pages_requested": meta.get("pages_requested", ""),
            "pages_failed": len(meta.get("pages_failed", []) or []),
            "scan_seconds": meta.get("elapsed_sec", scan_summary.get("elapsed_sec", "")),
            "watch": stats["watch"],
            "watch_only": stats["watch_only"],
            "qualified_only": stats["qualified_only"],
            "qualified_incl_high": stats["qualified_incl_high"],
            "high_only": stats["high_only"],
            "qualified_upper": stats["qualified_upper"],
            "high_upper": stats["high_upper"],
            "excluded": stats["excluded"],
            "union_deep_fetch": stats["union_deep_fetch"],
        }
        for reason in reason_keys:
            row[f"reason_{reason}"] = stats["reasons"].get(reason, 0)
        summary_rows.append(row)
    return summary_rows, stats_by_scope, reason_keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute tier summary from JSONL")
    parser.add_argument("--input", default=str(DATA_DIR / "universe_90d.jsonl"))
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    summary_path = DATA_DIR / "scan_summary.json"
    scan_summary = load_json(summary_path) if summary_path.exists() else {}
    summary_rows, stats_by_scope, reason_keys = build_rows(rows, scan_summary)

    fields = list(summary_rows[0].keys())
    write_csv(DATA_DIR / "tier_summary.csv", fields, summary_rows)

    if scan_summary:
        for scope, stats in stats_by_scope.items():
            if scope == "TOTAL":
                scan_summary["combined"] = stats
            elif scope in scan_summary.get("per_type", {}):
                scan_summary["per_type"][scope]["tiers"] = stats
        scan_summary["recomputed_at"] = iso_now()
        save_json(summary_path, scan_summary)

    for row in summary_rows:
        print(
            f"{row['scope']:>7}: total={row['fetched_unique']:>6} "
            f"watch={row['watch']:>5} (watch-only={row['watch_only']:>4}) "
            f"qualified_incl_high={row['qualified_incl_high']:>4} "
            f"high={row['high_only']:>3} excluded={row['excluded']:>6} "
            f"coverage={row['coverage_pct']:.2f}%"
        )
    print("reason columns:", ", ".join(reason_keys))


if __name__ == "__main__":
    main()
