"""Step 3 — scan the 90D universe (PUBLIC + SIGNAL) and apply the pre-filter."""
from __future__ import annotations

import argparse
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common import (
    DATA_DIR,
    ensure_dirs,
    iso_now,
    now_ms,
    save_json,
    write_csv,
    write_jsonl,
)
from fetch import BinanceBapiClient, list_rows, list_total
from tiering import (
    PRESETS,
    annotate_pre_score,
    evaluate_item,
    summarize_tiers,
)

TIER_ORDER = {"high_upper": 0, "qualified_upper": 1, "watch": 2, "excluded": 3}
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


def scan_type(
    client: BinanceBapiClient,
    portfolio_type: str,
    *,
    time_range: str,
    page_size: int,
    workers: int,
    max_passes: int = 2,
) -> dict:
    started = time.perf_counter()
    first = client.list_page(portfolio_type, 1, time_range, page_size)
    reported_total = list_total(first)
    rows: dict[str, dict] = {}
    pages_failed: list[int] = []
    pages_requested = 0
    max_reported_total = reported_total

    def collect(payload: dict) -> int:
        nonlocal max_reported_total
        max_reported_total = max(max_reported_total, list_total(payload))
        added = 0
        for row in list_rows(payload):
            pid = str(row.get("leadPortfolioId") or "")
            if not pid:
                continue
            if pid not in rows:
                rows[pid] = row
                added += 1
        return added

    collect(first)
    pages_requested += 1
    total_pages = max(1, math.ceil(max_reported_total / page_size))
    print(
        f"[scan:{portfolio_type}] reported_total={reported_total} "
        f"pages={total_pages} page_size={page_size}",
        flush=True,
    )

    pass_no = 1
    while True:
        if pass_no == 1:
            pages = list(range(2, total_pages + 1))
        else:
            pages = list(range(1, total_pages + 1))

        if pages:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(
                        client.list_page, portfolio_type, page, time_range, page_size
                    ): page
                    for page in pages
                }
                done = 0
                for future in as_completed(futures):
                    page = futures[future]
                    pages_requested += 1
                    done += 1
                    try:
                        payload = future.result()
                    except Exception as exc:  # noqa: BLE001 - log and continue
                        pages_failed.append(page)
                        print(
                            f"[scan:{portfolio_type}] page {page} failed: {exc}",
                            flush=True,
                        )
                        continue
                    collect(payload)
                    if done % 50 == 0 or done == len(pages):
                        coverage = (
                            len(rows) / max_reported_total * 100
                            if max_reported_total
                            else 0
                        )
                        print(
                            f"[scan:{portfolio_type}] pass {pass_no} "
                            f"{done}/{len(pages)} pages, unique={len(rows)}, "
                            f"coverage={coverage:.2f}%",
                            flush=True,
                        )

        coverage = len(rows) / max_reported_total if max_reported_total else 0.0
        if coverage >= 0.99 or pass_no >= max_passes:
            break
        # Lists shift while paging. A second pass usually closes the gap.
        total_pages = max(total_pages, math.ceil(max_reported_total / page_size))
        pass_no += 1
        print(
            f"[scan:{portfolio_type}] coverage {coverage * 100:.2f}% < 99%, "
            f"starting pass {pass_no}",
            flush=True,
        )

    elapsed = time.perf_counter() - started
    coverage = len(rows) / max_reported_total if max_reported_total else 0.0
    print(
        f"[scan:{portfolio_type}] done unique={len(rows)}/"
        f"{max_reported_total} ({coverage * 100:.2f}%) in {elapsed:.1f}s",
        flush=True,
    )
    return {
        "portfolio_type": portfolio_type,
        "reported_total": max_reported_total,
        "fetched_unique": len(rows),
        "coverage": round(coverage, 6),
        "pages_requested": pages_requested,
        "pages_failed": pages_failed,
        "elapsed_sec": round(elapsed, 2),
        "rows": list(rows.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 universe scan (90D)")
    parser.add_argument("--preset", default="balanced", choices=sorted(PRESETS))
    parser.add_argument("--types", default="PUBLIC,SIGNAL")
    parser.add_argument("--time-range", default="90D")
    parser.add_argument("--page-size", type=int, default=30)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-passes", type=int, default=2)
    parser.add_argument("--out", default=str(DATA_DIR / "universe_90d.jsonl"))
    args = parser.parse_args()

    ensure_dirs()
    aum_min = PRESETS[args.preset]
    types = [item.strip().upper() for item in args.types.split(",") if item.strip()]
    client = BinanceBapiClient()
    scan_started = time.perf_counter()
    start_iso = iso_now()
    current_ms = now_ms()

    per_type: dict[str, dict] = {}
    for portfolio_type in types:
        result = scan_type(
            client,
            portfolio_type,
            time_range=args.time_range,
            page_size=args.page_size,
            workers=args.workers,
            max_passes=args.max_passes,
        )
        evaluated = []
        for row in result["rows"]:
            item = dict(row)
            item.update(evaluate_item(row, current_ms, aum_min))
            evaluated.append(item)
        result["rows_evaluated"] = evaluated
        per_type[portfolio_type] = result

    # Combined universe, deduped by leadPortfolioId.
    combined: dict[str, dict] = {}
    for portfolio_type, result in per_type.items():
        for row in result["rows"]:
            pid = str(row.get("leadPortfolioId"))
            if pid not in combined:
                combined[pid] = dict(row)
                combined[pid]["_sources"] = [portfolio_type]
            else:
                sources = combined[pid].setdefault("_sources", [])
                if portfolio_type not in sources:
                    sources.append(portfolio_type)

    enriched = []
    for row in combined.values():
        evaluation = evaluate_item(row, current_ms, aum_min)
        enriched.append(
            {
                **row,
                "tier": evaluation["tier"],
                "potential_tier": evaluation["tier"],
                "tier_label": evaluation["tier_label"],
                "tier_reasons": evaluation["reasons"],
                "primary_reason": evaluation["primary_reason"],
                "missing_fields": evaluation["missing_fields"],
                "runtime_days": evaluation["runtime_days"],
                "traded_last_7d": evaluation["traded_last_7d"],
                "source_portfolio_type": ",".join(row.get("_sources") or []),
                "scan_time_range": args.time_range,
                "scan_ts": start_iso,
                "aum_min_preset": aum_min,
            }
        )

    enriched = annotate_pre_score(enriched, current_ms)
    enriched.sort(key=lambda r: (TIER_ORDER.get(r["potential_tier"], 9), str(r.get("leadPortfolioId"))))
    write_jsonl(args.out, enriched)

    # Per-scope summary rows.
    all_reason_keys = set(FIXED_REASONS)
    for result in per_type.values():
        all_reason_keys.update(summarize_tiers(result["rows_evaluated"])["reasons"].keys())
    all_reason_keys.update(summarize_tiers(enriched)["reasons"].keys())
    reason_keys = [r for r in FIXED_REASONS if r in all_reason_keys] + sorted(
        all_reason_keys - set(FIXED_REASONS)
    )

    summary_rows = []

    def add_summary(scope: str, stats: dict, meta: dict) -> None:
        row = {
            "scope": scope,
            "total_reported": meta.get("reported_total", stats["total"]),
            "fetched_unique": meta.get("fetched_unique", stats["total"]),
            "coverage_pct": round(meta.get("coverage", 1.0) * 100, 4),
            "pages_requested": meta.get("pages_requested", ""),
            "pages_failed": len(meta.get("pages_failed", []) or []),
            "scan_seconds": meta.get("elapsed_sec", ""),
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

    for portfolio_type, result in per_type.items():
        stats = summarize_tiers(result["rows_evaluated"])
        add_summary(portfolio_type, stats, result)
    total_stats = summarize_tiers(enriched)
    add_summary(
        "TOTAL",
        total_stats,
        {
            "reported_total": sum(r["reported_total"] for r in per_type.values()),
            "fetched_unique": len(enriched),
            "coverage": (
                len(enriched) / sum(r["reported_total"] for r in per_type.values())
                if per_type
                else 1.0
            ),
            "pages_requested": sum(r["pages_requested"] for r in per_type.values()),
            "pages_failed": [p for r in per_type.values() for p in r["pages_failed"]],
            "elapsed_sec": round(time.perf_counter() - scan_started, 2),
        },
    )

    fields = list(summary_rows[0].keys())
    write_csv(DATA_DIR / "tier_summary.csv", fields, summary_rows)

    # Detailed per-trader CSV for quick inspection.
    detail_fields = [
        "leadPortfolioId",
        "nickname",
        "portfolioType",
        "source_portfolio_type",
        "potential_tier",
        "tier_label",
        "primary_reason",
        "tier_reasons",
        "pre_score",
        "runtime_days",
        "traded_last_7d",
        "roi",
        "pnl",
        "mdd",
        "winRate",
        "sharpRatio",
        "aum",
        "copyAum",
        "copierPnl",
        "currentCopyCount",
        "maxCopyCount",
        "startTime",
        "lastTradeTime",
        "scan_ts",
    ]
    detail_rows = []
    for row in enriched:
        detail_rows.append(
            {
                **{key: row.get(key) for key in detail_fields if key in row},
                "tier_reasons": "|".join(row.get("tier_reasons") or []),
            }
        )
    write_csv(DATA_DIR / "universe_tiers.csv", detail_fields, detail_rows)

    summary = {
        "started_at": start_iso,
        "finished_at": iso_now(),
        "elapsed_sec": round(time.perf_counter() - scan_started, 2),
        "preset": args.preset,
        "aum_min": aum_min,
        "time_range": args.time_range,
        "page_size": args.page_size,
        "workers": args.workers,
        "types": types,
        "per_type": {
            key: {
                "reported_total": value["reported_total"],
                "fetched_unique": value["fetched_unique"],
                "coverage": value["coverage"],
                "pages_requested": value["pages_requested"],
                "pages_failed": value["pages_failed"],
                "elapsed_sec": value["elapsed_sec"],
                "tiers": summarize_tiers(value["rows_evaluated"]),
            }
            for key, value in per_type.items()
        },
        "combined": total_stats,
        "output": str(Path(args.out)),
        "note": (
            "B and A are subsets of Watch; union_deep_fetch is Watch, not B+A. "
            "Pre-score is only a deep-fetch ordering hint."
        ),
    }
    save_json(DATA_DIR / "scan_summary.json", summary)

    print("\n=== Tier summary ===")
    for row in summary_rows:
        print(
            f"{row['scope']:>7}: total={row['fetched_unique']:>6} "
            f"watch={row['watch']:>5} (watch-only={row['watch_only']:>4}) "
            f"qualified_incl_high={row['qualified_incl_high']:>4} "
            f"high={row['high_only']:>3} "
            f"excluded={row['excluded']:>6} coverage={row['coverage_pct']:.2f}%"
        )
    print(f"\nSaved: {args.out}")
    print(f"Saved: {DATA_DIR / 'tier_summary.csv'}")
    print(f"Saved: {DATA_DIR / 'universe_tiers.csv'}")
    print(f"Saved: {DATA_DIR / 'scan_summary.json'}")


if __name__ == "__main__":
    main()
