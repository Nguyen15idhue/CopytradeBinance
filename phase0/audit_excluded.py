"""Step 6 — audit 50 excluded traders for false negatives.

The prompt's core definition is intentionally simple:
    ACTIVE + not paused + ROI>0 + PnL>0 + totalOrder>=20 + copy slot open.

To avoid calling every intentional threshold a "false negative", this script
also reports:
  * fn_watch_eligible : the trader would pass the full Watch pre-filter if the
                        real detail/performance values were used.
  * fn_qualified      : the trader would pass the B thresholds.

Rates are reported separately. The go/no-go gate uses fn_watch_eligible.
"""
from __future__ import annotations

import argparse
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common import (
    DATA_DIR,
    RAW_DIR,
    ensure_dirs,
    iso_now,
    load_json,
    now_ms,
    read_jsonl,
    save_json,
    write_csv,
)
from fetch import BinanceBapiClient, response_data

FIELDS = [
    "portfolio_id",
    "tier",
    "primary_reason",
    "reasons",
    "status",
    "is_paused",
    "runtime_days",
    "perf_roi",
    "perf_pnl",
    "perf_mdd",
    "perf_win_rate",
    "perf_total_order",
    "perf_sharpe",
    "detail_aum",
    "detail_current_copies",
    "detail_max_copies",
    "slot_open",
    "actual_recent_7d",
    "fn_prompt",
    "fn_watch_eligible",
    "fn_qualified_eligible",
    "fetch_ok",
    "error",
]

REASON_ORDER = [
    "no_trade_7d",
    "runtime_lt_30",
    "roi_le_0",
    "pnl_le_0",
    "winrate_lt_40",
    "mdd_gt_40",
    "aum_lt_5000",
    "no_slots",
]


def _num(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stratified(items: list[dict], key_fn, n: int, rng: random.Random) -> list[dict]:
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


def select_audit(rows: list[dict], n: int, seed: int = 20261106) -> list[dict]:
    excluded = [r for r in rows if r.get("potential_tier") == "excluded"]
    rng = random.Random(seed)
    picked: list[dict] = []
    used: set[str] = set()

    # First, guarantee every reason has at least one representative.
    for reason in REASON_ORDER:
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
        picked.append(chosen)
        used.add(str(chosen.get("leadPortfolioId")))

    remaining = [
        row
        for row in excluded
        if str(row.get("leadPortfolioId")) not in used
    ]
    fill_n = max(0, n - len(picked))
    if fill_n:
        picked.extend(
            _stratified(
                remaining,
                lambda row: row.get("primary_reason") or "unknown",
                fill_n,
                rng,
            )
        )
    return picked[:n]


def audit_one(client: BinanceBapiClient, row: dict) -> dict:
    pid = str(row.get("leadPortfolioId"))
    outdir = RAW_DIR / "audit" / pid
    outdir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    detail = {}
    perf = {}

    try:
        payload = client.detail(pid)
        save_json(outdir / "detail.json", payload)
        detail = response_data(payload) or {}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"detail:{exc}")

    try:
        payload = client.performance(pid, "90D")
        save_json(outdir / "performance_90D.json", payload)
        perf = response_data(payload) or {}
    except Exception as exc:  # noqa: BLE001
        errors.append(f"performance:{exc}")

    runtime = None
    detail_start = _num(detail.get("startTime"))
    if detail_start:
        runtime = (now_ms() - detail_start) / 86_400_000.0

    current = _num(detail.get("currentCopyCount"))
    maximum = _num(detail.get("maxCopyCount"))
    slot_open = (
        current is not None
        and maximum is not None
        and maximum > 0
        and current < maximum
    )

    last_trade = _num(detail.get("lastTradeTime"))
    actual_recent = bool(last_trade and (now_ms() - last_trade) / 86_400_000.0 <= 7.0)

    roi = _num(perf.get("roi"))
    pnl = _num(perf.get("pnl"))
    mdd = _num(perf.get("mdd"))
    win_rate = _num(perf.get("winRate"))
    total_order = _num(perf.get("totalOrder"))
    sharpe = _num(perf.get("sharpRatio"))
    aum = _num(detail.get("aumAmount"))

    active = detail.get("status") == "ACTIVE" and detail.get("isPaused") is False
    prompt_ok = bool(
        active
        and roi is not None
        and roi > 0
        and pnl is not None
        and pnl > 0
        and total_order is not None
        and total_order >= 20
        and slot_open
    )
    watch_ok = bool(
        prompt_ok
        and runtime is not None
        and runtime >= 30
        and win_rate is not None
        and win_rate >= 40
        and mdd is not None
        and mdd <= 40
        and aum is not None
        and aum >= 5_000
        and actual_recent
    )
    qualified_ok = bool(
        active
        and runtime is not None
        and runtime >= 90
        and roi is not None
        and roi >= 10
        and win_rate is not None
        and win_rate >= 45
        and mdd is not None
        and mdd <= 30
        and aum is not None
        and aum >= 10_000
        and total_order is not None
        and total_order >= 50
        and (sharpe is None or sharpe >= 0.5)
        and slot_open
        and actual_recent
    )

    return {
        "portfolio_id": pid,
        "tier": row.get("potential_tier"),
        "primary_reason": row.get("primary_reason"),
        "reasons": "|".join(row.get("tier_reasons") or []),
        "status": detail.get("status"),
        "is_paused": detail.get("isPaused"),
        "runtime_days": None if runtime is None else round(runtime, 2),
        "perf_roi": roi,
        "perf_pnl": pnl,
        "perf_mdd": mdd,
        "perf_win_rate": win_rate,
        "perf_total_order": total_order,
        "perf_sharpe": sharpe,
        "detail_aum": aum,
        "detail_current_copies": current,
        "detail_max_copies": maximum,
        "slot_open": slot_open,
        "actual_recent_7d": actual_recent,
        "fn_prompt": prompt_ok,
        "fn_watch_eligible": watch_ok,
        "fn_qualified_eligible": qualified_ok,
        "fetch_ok": not errors,
        "error": "; ".join(errors),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 excluded audit")
    parser.add_argument("--universe", default=str(DATA_DIR / "universe_90d.jsonl"))
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20261106)
    args = parser.parse_args()

    ensure_dirs()
    rows = read_jsonl(args.universe)
    selected = select_audit(rows, args.n, args.seed)
    print(f"[audit] selected={len(selected)}", flush=True)
    print(
        "[audit] primary reasons:",
        dict(Counter(row.get("primary_reason") for row in selected)),
        flush=True,
    )

    client = BinanceBapiClient()
    started = time.perf_counter()
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(audit_one, client, row): row for row in selected}
        done = 0
        for future in as_completed(futures):
            done += 1
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                row = futures[future]
                results.append(
                    {
                        "portfolio_id": row.get("leadPortfolioId"),
                        "tier": row.get("potential_tier"),
                        "primary_reason": row.get("primary_reason"),
                        "reasons": "|".join(row.get("tier_reasons") or []),
                        "fetch_ok": False,
                        "error": str(exc),
                    }
                )
            if done % 10 == 0 or done == len(futures):
                print(f"[audit] {done}/{len(futures)}", flush=True)

    elapsed = time.perf_counter() - started
    results.sort(key=lambda r: str(r.get("portfolio_id")))
    write_csv(DATA_DIR / "audit_excluded.csv", FIELDS, results)

    fetched = [r for r in results if r.get("fetch_ok")]
    n_fetched = len(fetched)

    def rate(key: str) -> float | None:
        return round(sum(1 for r in fetched if r.get(key)) / n_fetched, 4) if n_fetched else None

    by_reason = {}
    for reason in sorted({str(r.get("primary_reason")) for r in fetched}):
        subset = [r for r in fetched if str(r.get("primary_reason")) == reason]
        by_reason[reason] = {
            "sampled": len(subset),
            "fn_prompt": sum(1 for r in subset if r.get("fn_prompt")),
            "fn_watch_eligible": sum(1 for r in subset if r.get("fn_watch_eligible")),
            "fn_qualified_eligible": sum(1 for r in subset if r.get("fn_qualified_eligible")),
        }

    summary = {
        "audited_at": iso_now(),
        "elapsed_sec": round(elapsed, 2),
        "selected": len(selected),
        "fetched": n_fetched,
        "failed": len(results) - n_fetched,
        "fn_prompt": sum(1 for r in fetched if r.get("fn_prompt")),
        "fn_prompt_rate": rate("fn_prompt"),
        "fn_watch_eligible": sum(1 for r in fetched if r.get("fn_watch_eligible")),
        "fn_watch_eligible_rate": rate("fn_watch_eligible"),
        "fn_qualified_eligible": sum(1 for r in fetched if r.get("fn_qualified_eligible")),
        "fn_qualified_eligible_rate": rate("fn_qualified_eligible"),
        "by_primary_reason": by_reason,
        "gate_metric": "fn_watch_eligible_rate",
        "gate_threshold": 0.05,
        "gate_passed": (rate("fn_watch_eligible") or 0) <= 0.05,
        "note": (
            "fn_prompt is the literal prompt definition. "
            "fn_watch_eligible additionally requires runtime>=30, WinRate>=40, "
            "MDD<=40, AUM>=5k and a real lastTradeTime within 7 days, so intentional "
            "threshold exclusions are not mislabelled as false negatives."
        ),
    }
    save_json(DATA_DIR / "audit_summary.json", summary)

    print(
        f"\n[audit] fetched={n_fetched}/{len(results)} in {elapsed:.1f}s | "
        f"fn_prompt={summary['fn_prompt']} ({summary['fn_prompt_rate']:.1%}) | "
        f"fn_watch={summary['fn_watch_eligible']} ({summary['fn_watch_eligible_rate']:.1%}) | "
        f"fn_qualified={summary['fn_qualified_eligible']} ({summary['fn_qualified_eligible_rate']:.1%})"
    )
    for reason, stats in by_reason.items():
        print(f"  {reason:>16}: {stats}")


if __name__ == "__main__":
    main()
