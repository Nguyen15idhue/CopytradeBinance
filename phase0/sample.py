"""Step 4 — choose the 70-trader Phase 0 sample.

Deliberate stratification, not a random dump:
  * A (high_upper)          : all available (13 live), capped at 20.
  * B (qualified_upper)     : 20 spread over Sharpe present/absent x CopyAum quartile.
  * C (watch)               : 20 spread over ROI quartile x MDD quartile.
  * Excluded                : 10, one or more per exclusion reason, fixture included.

The fixture 5296057151807357697 is mandatory even if the sampler would not pick it.
"""
from __future__ import annotations

import argparse
import bisect
import random
from collections import Counter, defaultdict

from common import DATA_DIR, ensure_dirs, read_jsonl, save_json, write_csv

FIXTURE_ID = "5296057151807357697"

MANIFEST_FIELDS = [
    "portfolio_id",
    "tier",
    "tier_label",
    "selection_stratum",
    "selection_note",
    "primary_reason",
    "filter_reasons",
    "source_portfolio_type",
    "roi",
    "pnl",
    "mdd",
    "win_rate",
    "sharpe",
    "aum",
    "copy_aum",
    "runtime_days",
    "current_copy_count",
    "max_copy_count",
    "pre_score",
    "is_fixture",
]


def _quartile(value, sorted_values: list[float]) -> str:
    if value is None or not sorted_values:
        return "na"
    pos = bisect.bisect_right(sorted_values, value) - 1
    bucket = min(3, max(0, int(pos * 4 / len(sorted_values))))
    return f"q{bucket + 1}"


def stratified_pick(items: list[dict], key_fn, n: int, rng: random.Random) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        buckets[key_fn(item)].append(item)
    for bucket in buckets.values():
        rng.shuffle(bucket)

    keys = sorted(buckets)
    picked: list[dict] = []
    cursor = 0
    while len(picked) < n and any(buckets[key] for key in keys):
        key = keys[cursor % len(keys)]
        if buckets[key]:
            picked.append(buckets[key].pop())
        cursor += 1
    return picked


def make_manifest_row(
    row: dict,
    tier: str,
    stratum: str,
    note: str,
    is_fixture: bool = False,
) -> dict:
    return {
        "portfolio_id": row.get("leadPortfolioId"),
        "tier": tier,
        "tier_label": row.get("tier_label"),
        "selection_stratum": stratum,
        "selection_note": note,
        "primary_reason": row.get("primary_reason"),
        "filter_reasons": "|".join(row.get("tier_reasons") or []),
        "source_portfolio_type": row.get("source_portfolio_type"),
        "roi": row.get("roi"),
        "pnl": row.get("pnl"),
        "mdd": row.get("mdd"),
        "win_rate": row.get("winRate"),
        "sharpe": row.get("sharpRatio"),
        "aum": row.get("aum"),
        "copy_aum": row.get("copyAum"),
        "runtime_days": row.get("runtime_days"),
        "current_copy_count": row.get("currentCopyCount"),
        "max_copy_count": row.get("maxCopyCount"),
        "pre_score": row.get("pre_score"),
        "is_fixture": "1" if is_fixture else "0",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Choose Phase 0 sample")
    parser.add_argument("--input", default=str(DATA_DIR / "universe_90d.jsonl"))
    parser.add_argument("--out", default=str(DATA_DIR / "sample_manifest.csv"))
    parser.add_argument("--seed", type=int, default=20261106)
    args = parser.parse_args()

    ensure_dirs()
    rows = read_jsonl(args.input)
    rng = random.Random(args.seed)

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row.get("potential_tier") or "excluded"].append(row)

    high = groups["high_upper"]
    qualified = groups["qualified_upper"]
    watch = groups["watch"]
    excluded = groups["excluded"]

    manifest: list[dict] = []

    # ---------------------------------------------------------------- tier A
    if len(high) <= 20:
        picked_a = sorted(high, key=lambda r: r.get("pre_score") or 0, reverse=True)
        note_a = f"high_upper={len(high)} <= 20; lấy toàn bộ."
    else:
        roi_values = sorted(
            v for v in (r.get("roi") for r in high) if v is not None
        )
        picked_a = stratified_pick(
            high, lambda r: _quartile(r.get("roi"), roi_values), 20, rng
        )
        note_a = "high_upper > 20; chọn trải đều ROI quartile."
    for row in picked_a:
        manifest.append(
            make_manifest_row(
                row,
                "A",
                "high_upper",
                note_a,
                is_fixture=str(row.get("leadPortfolioId")) == FIXTURE_ID,
            )
        )

    # ---------------------------------------------------------------- tier B
    copy_aum_values = sorted(
        v for v in (r.get("copyAum") for r in qualified) if v is not None
    )

    def b_stratum(row: dict) -> str:
        sharpe = "sharpe_null" if row.get("sharpRatio") is None else "sharpe_set"
        return f"{sharpe}|copyAum_{_quartile(row.get('copyAum'), copy_aum_values)}"

    picked_b = stratified_pick(qualified, b_stratum, 20, rng)
    note_b = (
        f"qualified_upper={len(qualified)}; chọn 20 theo Sharpe (có/null) "
        "x CopyAum quartile. Leverage chỉ kiểm tra sau position-history."
    )
    for row in picked_b:
        manifest.append(
            make_manifest_row(row, "B", b_stratum(row), note_b)
        )

    # ---------------------------------------------------------------- tier C
    roi_values_c = sorted(v for v in (r.get("roi") for r in watch) if v is not None)
    mdd_values_c = sorted(v for v in (r.get("mdd") for r in watch) if v is not None)

    def c_stratum(row: dict) -> str:
        return (
            f"roi_{_quartile(row.get('roi'), roi_values_c)}|"
            f"mdd_{_quartile(row.get('mdd'), mdd_values_c)}"
        )

    picked_c = stratified_pick(watch, c_stratum, 20, rng)
    note_c = (
        f"watch_only={len(watch)}; chọn 20 theo ROI quartile x MDD quartile."
    )
    for row in picked_c:
        manifest.append(
            make_manifest_row(row, "C", c_stratum(row), note_c)
        )

    # ------------------------------------------------------------- excluded
    def excluded_stratum(row: dict) -> str:
        return row.get("primary_reason") or "unknown"

    reason_order = [
        "no_trade_7d",
        "runtime_lt_30",
        "roi_le_0",
        "pnl_le_0",
        "winrate_lt_40",
        "mdd_gt_40",
        "aum_lt_5000",
        "no_slots",
    ]
    picked_x: list[tuple[dict, str]] = []
    used: set[str] = set()

    # One representative per exclusion reason, using ALL reasons (not only primary).
    for reason in reason_order:
        candidates = [
            row
            for row in excluded
            if reason in (row.get("tier_reasons") or [])
            and str(row.get("leadPortfolioId")) not in used
        ]
        if not candidates:
            continue
        candidates.sort(
            key=lambda row: (
                row.get("primary_reason") != reason,
                str(row.get("leadPortfolioId")),
            )
        )
        chosen = candidates[0]
        picked_x.append((chosen, f"coverage:{reason}"))
        used.add(str(chosen.get("leadPortfolioId")))

    fixture = next(
        (r for r in excluded if str(r.get("leadPortfolioId")) == FIXTURE_ID), None
    )
    if fixture is not None and FIXTURE_ID not in used:
        if len(picked_x) >= 10:
            dropped, _ = picked_x.pop()
            used.discard(str(dropped.get("leadPortfolioId")))
        picked_x.append((fixture, "mandatory_fixture"))
        used.add(FIXTURE_ID)

    # Fill up to 10 with diverse primary reasons.
    remaining = [
        row
        for row in excluded
        if str(row.get("leadPortfolioId")) not in used
    ]
    fill_n = max(0, 10 - len(picked_x))
    if fill_n:
        for row in stratified_pick(remaining, excluded_stratum, fill_n, rng):
            picked_x.append((row, f"fill:{excluded_stratum(row)}"))

    note_x = (
        "Chọn 10: một đại diện cho mỗi lý do loại (kể cả lý do phụ), "
        "sau đó fill theo primary_reason; bắt buộc có trader mẫu."
    )
    for row, stratum in picked_x:
        manifest.append(
            make_manifest_row(
                row,
                "excluded",
                stratum,
                note_x,
                is_fixture=str(row.get("leadPortfolioId")) == FIXTURE_ID,
            )
        )

    # A first, then B, C, excluded. Within a tier, higher pre_score first.
    tier_order = {"A": 0, "B": 1, "C": 2, "excluded": 3}
    manifest.sort(
        key=lambda r: (
            tier_order.get(r["tier"], 9),
            -(float(r["pre_score"]) if r["pre_score"] not in (None, "") else 0),
            str(r["portfolio_id"]),
        )
    )

    write_csv(args.out, MANIFEST_FIELDS, manifest)
    save_json(DATA_DIR / "sample_manifest.json", manifest)

    counts = Counter(r["tier"] for r in manifest)
    summary = {
        "seed": args.seed,
        "total_sample": len(manifest),
        "counts": dict(counts),
        "available": {
            "high_upper": len(high),
            "qualified_upper": len(qualified),
            "watch": len(watch),
            "excluded": len(excluded),
        },
        "fixture_id": FIXTURE_ID,
        "fixture_present": any(r["is_fixture"] == "1" for r in manifest),
        "notes": {
            "A": note_a,
            "B": note_b,
            "C": note_c,
            "excluded": note_x,
        },
        "excluded_strata": dict(Counter(r["selection_stratum"] for r in manifest if r["tier"] == "excluded")),
    }
    save_json(DATA_DIR / "sample_summary.json", summary)

    print(f"Sample total: {len(manifest)} -> {args.out}")
    for tier in ("A", "B", "C", "excluded"):
        print(f"  {tier:>8}: {counts.get(tier, 0)}")
    print(f"  fixture present: {summary['fixture_present']}")
    print(f"  excluded strata: {summary['excluded_strata']}")


if __name__ == "__main__":
    main()
