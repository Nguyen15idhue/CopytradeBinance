"""Measure raw concurrency behaviour: 1, 5 and 10 simultaneous list requests.

This intentionally bypasses the polite limiter so the rate-limit signal is real.
Only 16-32 requests are sent; no retries in this test.
"""
from __future__ import annotations

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from common import DATA_DIR, iso_now, save_json, write_csv
from fetch import BASE_F, HEADERS, is_rate_limit

FIELDS = [
    "batch",
    "concurrency",
    "request_index",
    "page",
    "http_status",
    "code",
    "elapsed_ms",
    "ok",
    "rate_limited",
    "error",
]


def one_request(page: int) -> dict:
    body = {
        "pageNumber": page,
        "pageSize": 30,
        "timeRange": "90D",
        "dataType": "ROI",
        "favoriteOnly": False,
        "hideFull": False,
        "nickname": "",
        "order": "DESC",
        "userAsset": 0,
        "portfolioType": "PUBLIC",
    }
    started = time.perf_counter()
    try:
        response = requests.post(
            BASE_F + "/home-page/query-list",
            headers=HEADERS,
            json=body,
            timeout=20,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        code = str(payload.get("code") or "")
        message = str(payload.get("message") or "")
        limited = is_rate_limit(response.status_code, code, message)
        return {
            "page": page,
            "http_status": response.status_code,
            "code": code,
            "elapsed_ms": elapsed_ms,
            "ok": response.status_code == 200
            and code in {"", "0", "000000"}
            and not limited,
            "rate_limited": limited,
            "error": "" if response.status_code == 200 else message,
        }
    except requests.RequestException as exc:
        return {
            "page": page,
            "http_status": "",
            "code": "",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "ok": False,
            "rate_limited": False,
            "error": str(exc),
        }


def run_batch(concurrency: int, batch: int) -> list[dict]:
    barrier = threading.Barrier(concurrency)

    def worker(index: int) -> dict:
        barrier.wait(timeout=10)
        result = one_request(index + 1)
        result.update({"batch": batch, "concurrency": concurrency, "request_index": index + 1})
        return result

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(worker, range(concurrency)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rate-limit concurrency test")
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    rows: list[dict] = []
    for batch in range(1, args.rounds + 1):
        for concurrency in (1, 5, 10):
            print(f"[rate] batch={batch} concurrency={concurrency}", flush=True)
            results = run_batch(concurrency, batch)
            rows.extend(results)
            time.sleep(1.5)

    write_csv(DATA_DIR / "rate_limit_test.csv", FIELDS, rows)

    summary = {"tested_at": iso_now(), "rounds": args.rounds, "batches": []}
    for batch in range(1, args.rounds + 1):
        for concurrency in (1, 5, 10):
            subset = [
                r
                for r in rows
                if r["batch"] == batch and r["concurrency"] == concurrency
            ]
            latencies = sorted(r["elapsed_ms"] for r in subset)
            summary["batches"].append(
                {
                    "batch": batch,
                    "concurrency": concurrency,
                    "requests": len(subset),
                    "ok": sum(1 for r in subset if r["ok"]),
                    "rate_limited": sum(1 for r in subset if r["rate_limited"]),
                    "failed": sum(1 for r in subset if not r["ok"]),
                    "max_elapsed_ms": max(latencies) if latencies else None,
                    "median_elapsed_ms": latencies[len(latencies) // 2] if latencies else None,
                }
            )
    summary["total_requests"] = len(rows)
    summary["total_rate_limited"] = sum(1 for r in rows if r["rate_limited"])
    summary["total_failed"] = sum(1 for r in rows if not r["ok"])
    save_json(DATA_DIR / "rate_limit_summary.json", summary)
    print(
        f"[rate] done requests={summary['total_requests']} "
        f"rate_limited={summary['total_rate_limited']} failed={summary['total_failed']}"
    )


if __name__ == "__main__":
    main()
