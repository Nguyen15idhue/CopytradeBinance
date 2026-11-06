"""Binance copy-trade BAPI client for Phase 0.

Endpoints were verified in the planning session on 2026-11-06:
  * list / detail / position / trade / transfer -> BASE_F
  * performance -> BASE_P (BASE_F returns 404)

The client is polite: 6 workers by default, a global minimum interval between
request starts, 20s timeout, and exponential backoff for rate-limit code 11012005.
"""
from __future__ import annotations

import argparse
import random
import threading
import time
from pathlib import Path
from typing import Any

import requests

from common import (
    DATA_DIR,
    FETCH_LOG,
    SMOKE_DIR,
    CsvLogger,
    ensure_dirs,
    iso_now,
    load_json,
    save_json,
)

BASE_F = "https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade"
BASE_P = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "clienttype": "web",
    "lang": "en",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/",
}

TIME_RANGES = ("7D", "30D", "90D", "180D")

LOG_FIELDS = [
    "ts",
    "endpoint",
    "portfolio_id",
    "page",
    "attempt",
    "http_status",
    "code",
    "elapsed_ms",
    "ok",
    "error",
]


class BapiError(RuntimeError):
    def __init__(
        self,
        endpoint: str,
        message: str,
        *,
        http_status: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(f"{endpoint}: HTTP={http_status} code={code} {message}")
        self.endpoint = endpoint
        self.http_status = http_status
        self.code = code
        self.message = message


def _code_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_rate_limit(http_status: int | None, code: str, message: str) -> bool:
    if http_status == 429:
        return True
    if code in {"11012005", "-1003", "1003"}:
        return True
    text = (message or "").lower()
    return any(token in text for token in ("too many", "rate limit", "frequent", "busy"))


class RateLimiter:
    """Global limiter: at most one request start every `min_interval` seconds."""

    def __init__(self, min_interval: float = 0.2) -> None:
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next_at:
                delay = self._next_at - now
            else:
                delay = 0.0
            self._next_at = max(now, self._next_at) + self.min_interval
        if delay > 0:
            time.sleep(delay)


class BinanceBapiClient:
    def __init__(
        self,
        *,
        timeout: int = 20,
        max_retries: int = 5,
        min_interval: float = 0.2,
        logger: CsvLogger | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self._limiter = RateLimiter(min_interval)
        self._local = threading.local()
        self._logger = logger or CsvLogger(FETCH_LOG, LOG_FIELDS)

    # ------------------------------------------------------------------ HTTP
    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            session.headers.update(HEADERS)
            self._local.session = session
        return session

    def _log(
        self,
        *,
        endpoint: str,
        portfolio_id: str | None,
        page: int | str | None,
        attempt: int,
        http_status: int | None,
        code: str,
        elapsed_ms: int,
        ok: bool,
        error: str = "",
    ) -> None:
        self._logger.log(
            {
                "ts": iso_now(),
                "endpoint": endpoint,
                "portfolio_id": portfolio_id or "",
                "page": "" if page is None else page,
                "attempt": attempt,
                "http_status": "" if http_status is None else http_status,
                "code": code,
                "elapsed_ms": elapsed_ms,
                "ok": "1" if ok else "0",
                "error": error,
            }
        )

    def _request(
        self,
        method: str,
        base: str,
        path: str,
        *,
        endpoint: str,
        params: dict | None = None,
        body: dict | None = None,
        portfolio_id: str | None = None,
        page: int | None = None,
    ) -> dict:
        url = base + path
        last_error: Exception | None = None
        max_attempts = self.max_retries + 1

        for attempt in range(1, max_attempts + 1):
            self._limiter.wait()
            started = time.perf_counter()
            http_status: int | None = None
            try:
                response = self._session().request(
                    method,
                    url,
                    params=params,
                    json=body,
                    timeout=self.timeout,
                )
                http_status = response.status_code
                elapsed_ms = int((time.perf_counter() - started) * 1000)

                if http_status in (408, 425, 429) or http_status >= 500:
                    raise requests.RequestException(f"retryable HTTP {http_status}")

                if http_status >= 400:
                    self._log(
                        endpoint=endpoint,
                        portfolio_id=portfolio_id,
                        page=page,
                        attempt=attempt,
                        http_status=http_status,
                        code="",
                        elapsed_ms=elapsed_ms,
                        ok=False,
                        error=f"HTTP {http_status}",
                    )
                    raise BapiError(
                        endpoint,
                        f"HTTP {http_status}",
                        http_status=http_status,
                    )

                try:
                    payload = response.json()
                except ValueError as exc:
                    self._log(
                        endpoint=endpoint,
                        portfolio_id=portfolio_id,
                        page=page,
                        attempt=attempt,
                        http_status=http_status,
                        code="",
                        elapsed_ms=elapsed_ms,
                        ok=False,
                        error=f"invalid json: {exc}",
                    )
                    raise BapiError(
                        endpoint, f"invalid JSON: {exc}", http_status=http_status
                    ) from exc

                code = _code_str(payload.get("code"))
                message = str(payload.get("message") or "")
                success = payload.get("success")

                if is_rate_limit(http_status, code, message):
                    self._log(
                        endpoint=endpoint,
                        portfolio_id=portfolio_id,
                        page=page,
                        attempt=attempt,
                        http_status=http_status,
                        code=code,
                        elapsed_ms=elapsed_ms,
                        ok=False,
                        error=f"rate limited: {message}",
                    )
                    raise requests.RequestException(f"rate limited: {code} {message}")

                if code not in {"", "0", "000000"} or success is False:
                    self._log(
                        endpoint=endpoint,
                        portfolio_id=portfolio_id,
                        page=page,
                        attempt=attempt,
                        http_status=http_status,
                        code=code,
                        elapsed_ms=elapsed_ms,
                        ok=False,
                        error=message,
                    )
                    raise BapiError(
                        endpoint,
                        message or "BAPI returned non-success",
                        http_status=http_status,
                        code=code,
                    )

                self._log(
                    endpoint=endpoint,
                    portfolio_id=portfolio_id,
                    page=page,
                    attempt=attempt,
                    http_status=http_status,
                    code=code,
                    elapsed_ms=elapsed_ms,
                    ok=True,
                )
                return payload

            except BapiError as exc:
                last_error = exc
                # Business errors are not retried.
                raise
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                if attempt < max_attempts:
                    backoff = min(2 ** attempt, 32) + random.uniform(0, 0.4)
                    self._log(
                        endpoint=endpoint,
                        portfolio_id=portfolio_id,
                        page=page,
                        attempt=attempt,
                        http_status=http_status,
                        code="",
                        elapsed_ms=elapsed_ms,
                        ok=False,
                        error=f"{exc}; retry in {backoff:.1f}s",
                    )
                    time.sleep(backoff)
                    continue
                self._log(
                    endpoint=endpoint,
                    portfolio_id=portfolio_id,
                    page=page,
                    attempt=attempt,
                    http_status=http_status,
                    code="",
                    elapsed_ms=elapsed_ms,
                    ok=False,
                    error=f"{exc}; exhausted retries",
                )

        raise BapiError(
            endpoint,
            f"exhausted {self.max_retries} retries: {last_error}",
        )

    # -------------------------------------------------------------- endpoints
    def list_page(
        self,
        portfolio_type: str = "PUBLIC",
        page: int = 1,
        time_range: str = "90D",
        page_size: int = 30,
    ) -> dict:
        body = {
            "pageNumber": page,
            "pageSize": page_size,
            "timeRange": time_range,
            "dataType": "ROI",
            "favoriteOnly": False,
            "hideFull": False,
            "nickname": "",
            "order": "DESC",
            "userAsset": 0,
            "portfolioType": portfolio_type,
        }
        return self._request(
            "POST",
            BASE_F,
            "/home-page/query-list",
            endpoint="list",
            body=body,
            page=page,
        )

    def detail(self, portfolio_id: str) -> dict:
        return self._request(
            "GET",
            BASE_F,
            "/lead-portfolio/detail",
            endpoint="detail",
            params={"portfolioId": portfolio_id},
            portfolio_id=portfolio_id,
        )

    def performance(self, portfolio_id: str, time_range: str = "90D") -> dict:
        return self._request(
            "GET",
            BASE_P,
            "/lead-portfolio/performance",
            endpoint=f"performance[{time_range}]",
            params={"portfolioId": portfolio_id, "timeRange": time_range},
            portfolio_id=portfolio_id,
        )

    def positions(
        self, portfolio_id: str, page: int = 1, page_size: int = 50
    ) -> dict:
        return self._request(
            "POST",
            BASE_F,
            "/lead-portfolio/position-history",
            endpoint="positions",
            body={
                "portfolioId": portfolio_id,
                "pageNumber": page,
                "pageSize": page_size,
            },
            portfolio_id=portfolio_id,
            page=page,
        )

    def trades(self, portfolio_id: str, page: int = 1, page_size: int = 200) -> dict:
        return self._request(
            "POST",
            BASE_F,
            "/lead-portfolio/trade-history",
            endpoint="trades",
            body={
                "portfolioId": portfolio_id,
                "pageNumber": page,
                "pageSize": page_size,
            },
            portfolio_id=portfolio_id,
            page=page,
        )

    def transfers(
        self, portfolio_id: str, page: int = 1, page_size: int = 50
    ) -> dict:
        return self._request(
            "POST",
            BASE_F,
            "/lead-portfolio/transfer-history",
            endpoint="transfers",
            body={
                "portfolioId": portfolio_id,
                "pageNumber": page,
                "pageSize": page_size,
            },
            portfolio_id=portfolio_id,
            page=page,
        )

    def probe(
        self,
        method: str,
        base: str,
        path: str,
        *,
        params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """One-shot probe that never raises; used to document missing endpoints."""
        self._limiter.wait()
        started = time.perf_counter()
        try:
            response = self._session().request(
                method, base + path, params=params, json=body, timeout=self.timeout
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            return {
                "method": method,
                "url": base + path,
                "http_status": response.status_code,
                "code": _code_str(payload.get("code")),
                "message": payload.get("message"),
                "elapsed_ms": elapsed_ms,
                "has_data": bool(payload.get("data")),
            }
        except requests.RequestException as exc:
            return {
                "method": method,
                "url": base + path,
                "http_status": None,
                "code": "",
                "message": str(exc),
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "has_data": False,
            }


# ------------------------------------------------------------------ helpers
def response_data(payload: dict) -> Any:
    return payload.get("data")


def list_rows(payload: dict) -> list[dict]:
    data = response_data(payload) or {}
    rows = data.get("list") if isinstance(data, dict) else None
    return rows or []


def list_total(payload: dict) -> int:
    data = response_data(payload) or {}
    try:
        return int(data.get("total") or 0)
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------- smoke
def smoke_test() -> dict:
    ensure_dirs()
    target = "5296057151807357697"
    client = BinanceBapiClient()
    summary: dict[str, Any] = {
        "started_at": iso_now(),
        "target_portfolio_id": target,
        "base_f": BASE_F,
        "base_p": BASE_P,
        "requests": {},
    }

    def run(label: str, fn, filename: str) -> Any:
        started = time.perf_counter()
        payload = fn()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        save_json(SMOKE_DIR / filename, payload)
        data = response_data(payload)
        item: dict[str, Any] = {
            "http_ok": True,
            "code": payload.get("code"),
            "elapsed_ms": elapsed_ms,
            "data_type": type(data).__name__,
        }
        if isinstance(data, dict):
            if "list" in data:
                item["list_len"] = len(data.get("list") or [])
                item["total"] = data.get("total")
            else:
                item["data_keys"] = sorted(data.keys())
        summary["requests"][label] = item
        print(f"[smoke] {label}: {elapsed_ms} ms, data={type(data).__name__}", flush=True)
        return payload

    run(
        "list_PUBLIC_p1",
        lambda: client.list_page("PUBLIC", 1),
        "list_PUBLIC_p1.json",
    )
    run(
        "list_SIGNAL_p1",
        lambda: client.list_page("SIGNAL", 1),
        "list_SIGNAL_p1.json",
    )
    run("detail", lambda: client.detail(target), "detail.json")

    windows: dict[str, Any] = {}
    for window in TIME_RANGES:
        windows[window] = run(
            f"performance_{window}",
            lambda w=window: client.performance(target, w),
            f"performance_{window}.json",
        )
    save_json(
        SMOKE_DIR / "performance_all_windows.json",
        {w: windows[w] for w in TIME_RANGES},
    )

    run(
        "positions_p1",
        lambda: client.positions(target, 1),
        "positions_p1.json",
    )
    run(
        "trades_p1",
        lambda: client.trades(target, 1),
        "trades_p1.json",
    )
    run(
        "transfers_p1",
        lambda: client.transfers(target, 1),
        "transfers_p1.json",
    )

    # Document endpoints that are expected to be unavailable.
    probe_specs = [
        ("GET", BASE_F, "/lead-portfolio/position", {"portfolioId": target}),
        ("GET", BASE_F, "/lead-portfolio/positions", {"portfolioId": target}),
        ("GET", BASE_F, "/lead-portfolio/current-position", {"portfolioId": target}),
        (
            "POST",
            BASE_F,
            "/lead-portfolio/copier-list",
            {"portfolioId": target, "pageNumber": 1, "pageSize": 20},
        ),
        (
            "POST",
            BASE_F,
            "/lead-portfolio/funding-history",
            {"portfolioId": target, "pageNumber": 1, "pageSize": 20},
        ),
        ("GET", BASE_P, "/lead-portfolio/funding-fee", {"portfolioId": target}),
    ]
    probes = []
    for method, base, path, payload_arg in probe_specs:
        if method == "GET":
            result = client.probe(method, base, path, params=payload_arg)
        else:
            result = client.probe(method, base, path, body=payload_arg)
        result["path"] = path
        probes.append(result)
        print(
            f"[probe] {method} {path}: HTTP={result['http_status']} "
            f"code={result['code']} has_data={result['has_data']}",
            flush=True,
        )
    summary["unavailable_probes"] = probes
    save_json(DATA_DIR / "unavailable_probe.json", probes)

    # Validation flags from the raw responses.
    perf_by_window = {w: response_data(windows[w]) or {} for w in TIME_RANGES}
    # detail was saved above; reload to keep the validation explicit
    detail_payload = load_json(SMOKE_DIR / "detail.json")
    detail_data = response_data(detail_payload) or {}

    list_public = response_data(load_json(SMOKE_DIR / "list_PUBLIC_p1.json")) or {}
    trades_payload = load_json(SMOKE_DIR / "trades_p1.json")
    trades_data = response_data(trades_payload) or {}

    summary["validation"] = {
        "performance_uses_base_p": True,
        "performance_windows_returned": list(perf_by_window.keys()),
        "list_page_size_requested": 30,
        "list_rows_returned": len(list_public.get("list") or []),
        "trade_page_size_requested": 200,
        "trade_rows_returned": len(trades_data.get("list") or []),
        "detail_status": detail_data.get("status"),
        "detail_portfolio_type": detail_data.get("portfolioType"),
        "detail_is_paused": detail_data.get("isPaused"),
        "detail_position_show": detail_data.get("positionShow"),
        "detail_start_time": detail_data.get("startTime"),
        "detail_last_trade_time": detail_data.get("lastTradeTime"),
        "chart_items_len_90d": None,
    }
    summary["finished_at"] = iso_now()
    save_json(DATA_DIR / "smoke_summary.json", summary)
    print("[smoke] saved phase0/data/smoke_summary.json", flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 BAPI client / smoke test")
    parser.add_argument("command", choices=["smoke", "probe", "list"], nargs="?", default="smoke")
    parser.add_argument("--type", default="PUBLIC", choices=["PUBLIC", "SIGNAL", "PRIVATE", "ALL"])
    parser.add_argument("--page", type=int, default=1)
    args = parser.parse_args()

    ensure_dirs()
    if args.command == "smoke":
        smoke_test()
    elif args.command == "probe":
        client = BinanceBapiClient()
        targets = [
            ("GET", BASE_F, "/lead-portfolio/position"),
            ("GET", BASE_F, "/lead-portfolio/positions"),
            ("GET", BASE_F, "/lead-portfolio/current-position"),
        ]
        for method, base, path in targets:
            print(client.probe(method, base, path, params={"portfolioId": "5296057151807357697"}))
    else:
        client = BinanceBapiClient()
        payload = client.list_page(args.type, args.page)
        print("total:", list_total(payload), "rows:", len(list_rows(payload)))


if __name__ == "__main__":
    main()
