"""Step 7 — verify the data-quality traps documented in the plan.

Checks, on the 63-trader sample:
  1. Published MDD vs naive MDD computed from chartItems.
  2. Order-based WinRate vs position-level WinRate.
  3. Sharpe null rate (universe + sample).
  4. AUM vs CopyAum.
  5. Lead PnL vs Copier PnL.
  6. Negative fees (rebates) in trade page 1.
  7. chartItems length, window equality for runtime < 30, and missing endpoints.

Outputs are evidence for the report, not production metrics.
"""
from __future__ import annotations

import argparse
import json
import statistics
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
    "status",
    "position_show",
    "positions_total",
    "closed_positions",
    "wins",
    "losses",
    "position_win_rate",
    "order_win_rate",
    "win_orders",
    "total_order",
    "order_win_rate_calc",
    "order_win_rate_diff",
    "mdd_published",
    "mdd_naive_chart",
    "mdd_diff_pp",
    "sharpe_list",
    "sharpe_perf",
    "aum",
    "copy_aum",
    "copy_aum_ratio",
    "lead_pnl",
    "copier_pnl",
    "copier_pnl_ratio",
    "fees_page1",
    "negative_fees_page1",
    "chart_len",
    "windows_equal",
]


def _num(value):
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _median(values):
    clean = [v for v in values if v is not None]
    return round(statistics.median(clean), 4) if clean else None


def naive_mdd(chart_items: list[dict]) -> float | None:
    values = []
    for point in chart_items or []:
        value = _num(point.get("value")) if isinstance(point, dict) else None
        if value is not None:
            values.append(value)
    if len(values) < 2:
        return None
    equity = [1.0 + value / 100.0 for value in values]
    peak = equity[0]
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)
    return round(max_dd * 100.0, 4)


def perf_window(path: Path, window: str) -> dict:
    if not path.exists():
        return {}
    payload = load_json(path)
    windows = payload.get("windows") or {}
    entry = windows.get(window) or {}
    return entry.get("data") or {}


def detail_data(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_json(path).get("data") or {}


def positions_data(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_json(path)


def trade_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = load_json(path)
    return (payload.get("data") or {}).get("list") or []


def main() -> None:
    parser = argparse.ArgumentParser(description="Indicator quality checks")
    parser.add_argument("--universe", default=str(DATA_DIR / "universe_90d.jsonl"))
    parser.add_argument("--manifest", default=str(DATA_DIR / "sample_manifest.csv"))
    args = parser.parse_args()

    universe_rows = read_jsonl(args.universe)
    universe = {str(r.get("leadPortfolioId")): r for r in universe_rows}
    manifest = read_csv(args.manifest)

    rows = []
    for item in manifest:
        pid = str(item.get("portfolio_id"))
        tier = str(item.get("tier"))
        base = RAW_DIR / tier / pid
        source = universe.get(pid) or {}
        detail = detail_data(base / "detail.json")
        perf = perf_window(base / "performance.json", "90D")
        positions = positions_data(base / "positions.json")
        trades = trade_rows(base / "trades_page1.json")

        runtime = _num(source.get("runtime_days"))
        if runtime is None:
            start = _num(detail.get("startTime"))
            runtime = (now_ms() - start) / 86_400_000.0 if start else None

        position_rows = positions.get("list") or []
        wins = sum(1 for p in position_rows if (_num(p.get("closingPnl")) or 0) > 0)
        losses = sum(1 for p in position_rows if (_num(p.get("closingPnl")) or 0) < 0)
        closed = wins + losses
        position_win_rate = round(wins / closed * 100.0, 4) if closed else None

        order_win_rate = _num(perf.get("winRate"))
        win_orders = _num(perf.get("winOrders"))
        total_order = _num(perf.get("totalOrder"))
        order_calc = (
            round(win_orders / total_order * 100.0, 4)
            if win_orders is not None and total_order
            else None
        )
        order_diff = (
            round(order_win_rate - order_calc, 4)
            if order_win_rate is not None and order_calc is not None
            else None
        )

        published_mdd = _num(perf.get("mdd"))
        if published_mdd is None:
            published_mdd = _num(source.get("mdd"))
        chart = source.get("chartItems") or []
        mdd_naive = naive_mdd(chart)
        mdd_diff = (
            round(mdd_naive - published_mdd, 4)
            if mdd_naive is not None and published_mdd is not None
            else None
        )

        aum = _num(detail.get("aumAmount"))
        if aum is None:
            aum = _num(source.get("aum"))
        copy_aum = _num(detail.get("copyAum"))
        if copy_aum is None:
            copy_aum = _num(source.get("copyAum"))
        copy_ratio = (
            round(copy_aum / aum, 6)
            if copy_aum is not None and aum not in (None, 0)
            else None
        )

        lead_pnl = _num(perf.get("pnl"))
        copier_pnl = _num(perf.get("copierPnl"))
        copier_ratio = (
            round(copier_pnl / lead_pnl, 6)
            if copier_pnl is not None and lead_pnl not in (None, 0)
            else None
        )

        fees = [_num(t.get("fee")) for t in trades]
        fees = [f for f in fees if f is not None]
        total_fees = round(sum(fees), 6) if fees else None
        negative_fees = sum(1 for f in fees if f < 0)

        # Window equality for very young portfolios.
        windows_equal = None
        if runtime is not None and runtime < 30:
            keys = ("roi", "pnl", "mdd", "copierPnl", "winRate", "totalOrder")
            signatures = []
            for window in ("7D", "30D", "90D", "180D"):
                data = perf_window(base / "performance.json", window)
                signatures.append(tuple(_num(data.get(key)) for key in keys))
            windows_equal = all(sig == signatures[0] for sig in signatures)

        rows.append(
            {
                "portfolio_id": pid,
                "tier": tier,
                "runtime_days": runtime,
                "status": detail.get("status"),
                "position_show": detail.get("positionShow"),
                "positions_total": positions.get("total"),
                "closed_positions": closed,
                "wins": wins,
                "losses": losses,
                "position_win_rate": position_win_rate,
                "order_win_rate": order_win_rate,
                "win_orders": win_orders,
                "total_order": total_order,
                "order_win_rate_calc": order_calc,
                "order_win_rate_diff": order_diff,
                "mdd_published": published_mdd,
                "mdd_naive_chart": mdd_naive,
                "mdd_diff_pp": mdd_diff,
                "sharpe_list": _num(source.get("sharpRatio")),
                "sharpe_perf": _num(perf.get("sharpRatio")),
                "aum": aum,
                "copy_aum": copy_aum,
                "copy_aum_ratio": copy_ratio,
                "lead_pnl": lead_pnl,
                "copier_pnl": copier_pnl,
                "copier_pnl_ratio": copier_ratio,
                "fees_page1": total_fees,
                "negative_fees_page1": negative_fees,
                "chart_len": len(chart),
                "windows_equal": windows_equal,
            }
        )

    write_csv(DATA_DIR / "indicator_quality.csv", FIELDS, rows)

    # ------------------------------------------------------------- aggregates
    mdd_pairs = [r for r in rows if r["mdd_diff_pp"] is not None]
    mdd_diffs = [abs(r["mdd_diff_pp"]) for r in mdd_pairs]
    winrate_pairs = [
        r
        for r in rows
        if r["position_win_rate"] is not None and r["order_win_rate"] is not None
    ]
    winrate_diffs = [
        abs(r["position_win_rate"] - r["order_win_rate"]) for r in winrate_pairs
    ]
    copy_ratios = [r["copy_aum_ratio"] for r in rows if r["copy_aum_ratio"] is not None]
    copier_ratios = [
        r["copier_pnl_ratio"] for r in rows if r["copier_pnl_ratio"] is not None
    ]
    negative_fee_traders = [r for r in rows if r["negative_fees_page1"] > 0]
    young = [r for r in rows if r["windows_equal"] is not None]

    universe_sharpe_null = sum(
        1 for r in universe_rows if _num(r.get("sharpRatio")) is None
    )
    sample_sharpe_null = sum(1 for r in rows if r["sharpe_perf"] is None)

    probe_path = DATA_DIR / "unavailable_probe.json"
    probes = load_json(probe_path) if probe_path.exists() else []
    probe_404 = sum(1 for p in probes if p.get("http_status") == 404)

    position_show_false = [r for r in rows if r["position_show"] is False]
    position_show_false_with_positions = [
        r for r in position_show_false if (r["positions_total"] or 0) > 0
    ]

    mdd_examples = sorted(
        (r for r in mdd_pairs if (r["mdd_diff_pp"] or 0) > 5),
        key=lambda r: abs(r["mdd_diff_pp"]),
        reverse=True,
    )[:5]
    winrate_examples = sorted(
        winrate_pairs,
        key=lambda r: abs(r["position_win_rate"] - r["order_win_rate"]),
        reverse=True,
    )[:5]

    summary = {
        "sample_size": len(rows),
        "mdd": {
            "compared": len(mdd_pairs),
            "median_abs_diff_pp": _median(mdd_diffs),
            "max_abs_diff_pp": round(max(mdd_diffs), 4) if mdd_diffs else None,
            "count_diff_gt_1pp": sum(1 for d in mdd_diffs if d > 1),
            "count_diff_gt_5pp": sum(1 for d in mdd_diffs if d > 5),
            "examples": [
                {
                    "portfolio_id": r["portfolio_id"],
                    "tier": r["tier"],
                    "published": r["mdd_published"],
                    "naive_chart": r["mdd_naive_chart"],
                    "diff_pp": r["mdd_diff_pp"],
                }
                for r in mdd_examples
            ],
        },
        "win_rate": {
            "compared": len(winrate_pairs),
            "median_abs_diff_pp": _median(winrate_diffs),
            "max_abs_diff_pp": round(max(winrate_diffs), 4) if winrate_diffs else None,
            "count_diff_gt_5pp": sum(1 for d in winrate_diffs if d > 5),
            "examples": [
                {
                    "portfolio_id": r["portfolio_id"],
                    "tier": r["tier"],
                    "order_win_rate": r["order_win_rate"],
                    "position_win_rate": r["position_win_rate"],
                    "closed_positions": r["closed_positions"],
                }
                for r in winrate_examples
            ],
            "order_vs_calc_max_diff": max(
                (abs(r["order_win_rate_diff"]) for r in rows if r["order_win_rate_diff"] is not None),
                default=None,
            ),
        },
        "sharpe": {
            "universe_rows": len(universe_rows),
            "universe_null": universe_sharpe_null,
            "universe_null_rate": round(universe_sharpe_null / len(universe_rows), 4)
            if universe_rows
            else None,
            "sample_size": len(rows),
            "sample_null": sample_sharpe_null,
            "sample_null_rate": round(sample_sharpe_null / len(rows), 4) if rows else None,
        },
        "aum_vs_copy_aum": {
            "compared": len(copy_ratios),
            "median_copy_ratio": _median(copy_ratios),
            "count_copy_lt_5pct": sum(1 for v in copy_ratios if v < 0.05),
            "count_copy_lt_1pct": sum(1 for v in copy_ratios if v < 0.01),
        },
        "lead_vs_copier_pnl": {
            "compared": len(copier_ratios),
            "median_copier_ratio": _median(copier_ratios),
            "count_copier_lt_1pct": sum(1 for v in copier_ratios if v < 0.01),
            "count_copier_negative": sum(1 for r in rows if (r["copier_pnl"] or 0) < 0),
        },
        "fees": {
            "traders_checked": sum(1 for r in rows if r["fees_page1"] is not None),
            "traders_with_negative_fee": len(negative_fee_traders),
            "traders_with_zero_fee_only": sum(
                1
                for r in rows
                if r["fees_page1"] == 0 and r["negative_fees_page1"] == 0
            ),
            "sum_fees_page1": round(
                sum(r["fees_page1"] for r in rows if r["fees_page1"] is not None), 4
            ),
            "examples": [
                {
                    "portfolio_id": r["portfolio_id"],
                    "fees_page1": r["fees_page1"],
                    "negative_fills": r["negative_fees_page1"],
                }
                for r in negative_fee_traders[:5]
            ],
        },
        "chart_items": {
            "sample_size": len(rows),
            "len_90": sum(1 for r in rows if r["chart_len"] == 90),
            "min_len": min((r["chart_len"] for r in rows), default=None),
            "max_len": max((r["chart_len"] for r in rows), default=None),
            "universe_len_90": sum(
                1 for r in universe_rows if len(r.get("chartItems") or []) == 90
            ),
        },
        "young_portfolio_windows": {
            "checked": len(young),
            "all_windows_equal": sum(1 for r in young if r["windows_equal"]),
            "examples": [
                {"portfolio_id": r["portfolio_id"], "runtime_days": r["runtime_days"]}
                for r in young[:5]
            ],
        },
        "missing_endpoints": {
            "probes": len(probes),
            "http_404": probe_404,
            "paths": [p.get("path") for p in probes if p.get("http_status") == 404],
        },
        "position_show": {
            "false_count": len(position_show_false),
            "false_but_positions_fetched": len(position_show_false_with_positions),
            "note": "positionShow=false does not block position-history.",
        },
    }
    save_json(DATA_DIR / "indicator_quality_summary.json", summary)

    print(f"[quality] sample={len(rows)}")
    print(
        f"  MDD: compared={summary['mdd']['compared']} "
        f"median_abs_diff={summary['mdd']['median_abs_diff_pp']}pp "
        f">1pp={summary['mdd']['count_diff_gt_1pp']} "
        f">5pp={summary['mdd']['count_diff_gt_5pp']}"
    )
    print(
        f"  WinRate: compared={summary['win_rate']['compared']} "
        f"median_abs_diff={summary['win_rate']['median_abs_diff_pp']}pp "
        f">5pp={summary['win_rate']['count_diff_gt_5pp']}"
    )
    print(
        f"  Sharpe null: universe={summary['sharpe']['universe_null_rate']:.1%} "
        f"sample={summary['sharpe']['sample_null_rate']:.1%}"
    )
    print(
        f"  CopyAum/AUM median={summary['aum_vs_copy_aum']['median_copy_ratio']} "
        f"<5%={summary['aum_vs_copy_aum']['count_copy_lt_5pct']}"
    )
    print(
        f"  CopierPnl/LeadPnl median={summary['lead_vs_copier_pnl']['median_copier_ratio']} "
        f"<1%={summary['lead_vs_copier_pnl']['count_copier_lt_1pct']}"
    )
    print(
        f"  Negative fee traders={summary['fees']['traders_with_negative_fee']}/"
        f"{summary['fees']['traders_checked']}"
    )
    print(
        f"  chartItems len=90: {summary['chart_items']['len_90']}/{len(rows)} | "
        f"young windows equal={summary['young_portfolio_windows']['all_windows_equal']}/"
        f"{summary['young_portfolio_windows']['checked']}"
    )
    print(
        f"  Missing endpoints 404: {summary['missing_endpoints']['http_404']}/"
        f"{summary['missing_endpoints']['probes']}"
    )


if __name__ == "__main__":
    main()
