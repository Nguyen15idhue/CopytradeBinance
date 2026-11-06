"""Step 5 — deep fetch the sample (detail, 4 performance windows, positions,
transfers, trade-history page 1 only).

Raw responses are kept exactly as returned. Trade history is deliberately
limited to page 1 (200 fills); full history is out of scope for Phase 0.
"""
from __future__ import annotations

import argparse
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common import (
    DATA_DIR,
    RAW_DIR,
    ensure_dirs,
    iso_now,
    read_csv,
    save_json,
    write_csv,
)
from fetch import TIME_RANGES, BinanceBapiClient, response_data

STATUS_FIELDS = [
    "portfolio_id",
    "tier",
    "ok",
    "endpoints_ok",
    "endpoints_failed",
    "detail_status",
    "detail_is_paused",
    "detail_position_show",
    "positions_total",
    "trades_total_reported",
    "trades_page1_rows",
    "transfers_total",
    "elapsed_sec",
    "error",
]

MAX_POSITION_PAGES = 20
MAX_TRANSFER_PAGES = 20


def _paged_all(
    fetch_page,
    *,
    page_size: int,
    max_pages: int,
) -> dict:
    pages = []
    rows: list[dict] = []
    total = 0
    page = 1
    while page <= max_pages:
        payload = fetch_page(page)
        data = response_data(payload) or {}
        total = int(data.get("total") or 0)
        page_rows = data.get("list") or []
        pages.append(payload)
        rows.extend(page_rows)
        if not page_rows or len(rows) >= total:
            break
        page += 1
    return {"total": total, "list": rows, "pages": pages, "page_size": page_size}


def process_one(client: BinanceBapiClient, row: dict, *, resume: bool) -> dict:
    pid = str(row.get("portfolio_id"))
    tier = str(row.get("tier") or "unknown")
    outdir = RAW_DIR / tier / pid
    outdir.mkdir(parents=True, exist_ok=True)

    required = [
        "detail.json",
        "performance.json",
        "positions.json",
        "transfers.json",
        "trades_page1.json",
    ]
    if resume and all((outdir / name).exists() for name in required):
        return {
            "portfolio_id": pid,
            "tier": tier,
            "ok": "1",
            "endpoints_ok": "skipped_existing",
            "endpoints_failed": "",
            "detail_status": "",
            "detail_is_paused": "",
            "detail_position_show": "",
            "positions_total": "",
            "trades_total_reported": "",
            "trades_page1_rows": "",
            "transfers_total": "",
            "elapsed_sec": 0,
            "error": "",
        }

    started = time.perf_counter()
    ok: list[str] = []
    failed: list[str] = []
    detail_status = ""
    detail_is_paused = ""
    detail_position_show = ""
    positions_total = 0
    trades_total = 0
    trades_rows = 0
    transfers_total = 0

    # Keep the list row with the raw bundle for offline checks.
    save_json(outdir / "list_row.json", row)

    try:
        detail_payload = client.detail(pid)
        save_json(outdir / "detail.json", detail_payload)
        detail = response_data(detail_payload) or {}
        detail_status = detail.get("status") or ""
        detail_is_paused = detail.get("isPaused")
        detail_position_show = detail.get("positionShow")
        ok.append("detail")
    except Exception as exc:  # noqa: BLE001
        failed.append(f"detail:{exc}")

    try:
        windows = {}
        for window in TIME_RANGES:
            windows[window] = client.performance(pid, window)
        save_json(
            outdir / "performance.json",
            {
                "portfolio_id": pid,
                "fetched_at": iso_now(),
                "windows": windows,
            },
        )
        ok.append("performance")
    except Exception as exc:  # noqa: BLE001
        failed.append(f"performance:{exc}")

    try:
        positions = _paged_all(
            lambda page: client.positions(pid, page, 50),
            page_size=50,
            max_pages=MAX_POSITION_PAGES,
        )
        positions["portfolio_id"] = pid
        positions["fetched_at"] = iso_now()
        save_json(outdir / "positions.json", positions)
        positions_total = positions["total"]
        ok.append("positions")
    except Exception as exc:  # noqa: BLE001
        failed.append(f"positions:{exc}")

    try:
        transfers = _paged_all(
            lambda page: client.transfers(pid, page, 50),
            page_size=50,
            max_pages=MAX_TRANSFER_PAGES,
        )
        transfers["portfolio_id"] = pid
        transfers["fetched_at"] = iso_now()
        save_json(outdir / "transfers.json", transfers)
        transfers_total = transfers["total"]
        ok.append("transfers")
    except Exception as exc:  # noqa: BLE001
        failed.append(f"transfers:{exc}")

    try:
        trades_payload = client.trades(pid, 1, 200)
        save_json(outdir / "trades_page1.json", trades_payload)
        trades_data = response_data(trades_payload) or {}
        trades_total = int(trades_data.get("total") or 0)
        trades_rows = len(trades_data.get("list") or [])
        ok.append("trades_page1")
    except Exception as exc:  # noqa: BLE001
        failed.append(f"trades_page1:{exc}")

    elapsed = time.perf_counter() - started
    return {
        "portfolio_id": pid,
        "tier": tier,
        "ok": "1" if not failed else "0",
        "endpoints_ok": "|".join(ok),
        "endpoints_failed": "|".join(failed),
        "detail_status": detail_status,
        "detail_is_paused": detail_is_paused,
        "detail_position_show": detail_position_show,
        "positions_total": positions_total,
        "trades_total_reported": trades_total,
        "trades_page1_rows": trades_rows,
        "transfers_total": transfers_total,
        "elapsed_sec": round(elapsed, 2),
        "error": "" if not failed else "; ".join(failed),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 deep fetch")
    parser.add_argument("--manifest", default=str(DATA_DIR / "sample_manifest.csv"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--tiers", default="")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    rows = read_csv(args.manifest)
    if args.tiers:
        allowed = {t.strip() for t in args.tiers.split(",") if t.strip()}
        rows = [r for r in rows if r.get("tier") in allowed]
    if args.limit:
        rows = rows[: args.limit]

    client = BinanceBapiClient()
    started = time.perf_counter()
    statuses: list[dict] = []
    total = len(rows)
    print(f"[deep] traders={total} workers={args.workers}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                process_one, client, row, resume=not args.no_resume
            ): row
            for row in rows
        }
        done = 0
        for future in as_completed(futures):
            row = futures[future]
            done += 1
            try:
                status = future.result()
            except Exception as exc:  # noqa: BLE001
                status = {
                    "portfolio_id": row.get("portfolio_id"),
                    "tier": row.get("tier"),
                    "ok": "0",
                    "endpoints_ok": "",
                    "endpoints_failed": "fatal",
                    "detail_status": "",
                    "detail_is_paused": "",
                    "detail_position_show": "",
                    "positions_total": "",
                    "trades_total_reported": "",
                    "trades_page1_rows": "",
                    "transfers_total": "",
                    "elapsed_sec": 0,
                    "error": str(exc),
                }
            statuses.append(status)
            print(
                f"[deep] {done}/{total} pid={status['portfolio_id']} "
                f"tier={status['tier']} ok={status['ok']} "
                f"failed={status['endpoints_failed'][:80]}",
                flush=True,
            )

    elapsed = time.perf_counter() - started
    statuses.sort(key=lambda r: (str(r.get("tier")), str(r.get("portfolio_id"))))
    write_csv(DATA_DIR / "deep_fetch_status.csv", STATUS_FIELDS, statuses)

    failed_counts = Counter()
    for status in statuses:
        if status.get("endpoints_failed") and status["endpoints_failed"] != "skipped_existing":
            failed_counts[status["endpoints_failed"].split(":")[0]] += 1

    summary = {
        "started_at": iso_now(),
        "elapsed_sec": round(elapsed, 2),
        "traders": len(statuses),
        "ok": sum(1 for s in statuses if s.get("ok") == "1"),
        "failed": sum(1 for s in statuses if s.get("ok") != "1"),
        "by_tier": dict(Counter(str(s.get("tier")) for s in statuses)),
        "failed_endpoint_groups": dict(failed_counts),
        "raw_dir": str(RAW_DIR),
        "note": "Trade history is page 1 only (max 200 fills). Full history is out of Phase 0 scope.",
    }
    save_json(DATA_DIR / "deep_fetch_summary.json", summary)

    print(
        f"\n[deep] done in {elapsed:.1f}s | ok={summary['ok']} "
        f"failed={summary['failed']} | {RAW_DIR}"
    )


if __name__ == "__main__":
    main()
