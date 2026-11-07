"""HTTP client cho BAPI: timeout, retry/backoff, circuit breaker."""

import asyncio
import logging
import random
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

RATE_LIMIT_CODES = {"11012005", "-1003", "1003"}
OK_CODES = {"", "0", "000000"}


class BapiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retry_after: float | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"BAPI {status_code} [{code}]: {message}")


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


class CircuitOpenError(BapiError):
    def __init__(self) -> None:
        super().__init__(503, "CIRCUIT_OPEN", "Circuit breaker đang mở, tạm dừng gọi BAPI")


class CircuitBreaker:
    """Mở sau `threshold` lỗi liên tiếp, half-open sau `reset_seconds`."""

    def __init__(self, threshold: int = 5, reset_seconds: float = 60.0) -> None:
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self.reset_seconds:
            return False  # half-open: cho thử lại
        return True

    def allow(self) -> bool:
        return not self.is_open

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.threshold:
            self._opened_at = time.monotonic()


class BapiHttpClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        concurrency: int | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        breaker: CircuitBreaker | None = None,
        sleep: Any | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.bapi_base_url).rstrip("/")
        self.timeout = timeout or settings.bapi_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else settings.bapi_max_retries
        self._semaphore = asyncio.Semaphore(concurrency or settings.bapi_concurrency)
        self._transport = transport
        self.breaker = breaker or CircuitBreaker()
        self._sleep = sleep or asyncio.sleep
        self._cooldown_until = 0.0
        self._client: httpx.AsyncClient | None = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                transport=self._transport,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CopytradeBinance/0.1)",
                    "Content-Type": "application/json",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/",
                },
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BapiHttpClient":
        self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        if not self.breaker.allow():
            raise CircuitOpenError()
        client = self._ensure_client()

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            await self._wait_for_cooldown()
            try:
                async with self._semaphore:
                    response = await client.request(method, path, params=params, json=json)
                if response.status_code == 429:
                    raise BapiError(
                        429,
                        "RATE_LIMITED",
                        "BAPI chặn tần suất (HTTP 429)",
                        retry_after=_retry_after_seconds(response),
                    )
                payload = self._parse_json(response)
                code = str(payload.get("code", ""))
                if response.status_code >= 500 or code in RATE_LIMIT_CODES:
                    raise BapiError(
                        response.status_code, code or "HTTP_5XX", "Lỗi tạm thời từ BAPI"
                    )
                if response.status_code >= 400:
                    raise BapiError(
                        response.status_code,
                        code or "HTTP_ERROR",
                        str(payload.get("message") or "BAPI trả lỗi"),
                    )
                if code not in OK_CODES or payload.get("success") is False:
                    self.breaker.record_failure()
                    raise BapiError(
                        response.status_code,
                        code or "NON_SUCCESS",
                        str(payload.get("message") or "BAPI trả non-success"),
                    )
                self.breaker.record_success()
                return payload.get("data")
            except (httpx.TimeoutException, httpx.TransportError, BapiError) as exc:
                is_rate_limited = isinstance(exc, BapiError) and (
                    exc.code == "RATE_LIMITED" or exc.code in RATE_LIMIT_CODES
                )
                retryable = (
                    isinstance(exc, (httpx.TimeoutException, httpx.TransportError))
                    or (isinstance(exc, BapiError) and exc.status_code >= 500)
                    or (isinstance(exc, BapiError) and exc.code in RATE_LIMIT_CODES)
                    or is_rate_limited
                )
                if not retryable or attempt >= self.max_retries:
                    if isinstance(exc, BapiError):
                        if exc.status_code >= 500 or is_rate_limited:
                            self.breaker.record_failure()
                    else:
                        self.breaker.record_failure()
                    raise
                last_error = exc
                if is_rate_limited:
                    wait = max(30.0, min(exc.retry_after or 30.0, 120.0))
                    delay = min(wait * (attempt + 1), 180.0)
                else:
                    delay = min(2 ** (attempt + 1), 16)
                delay += random.uniform(0, 0.5)
                if is_rate_limited:
                    self._cooldown_until = max(
                        self._cooldown_until, time.monotonic() + delay
                    )
                logger.warning(
                    "BAPI lỗi tạm thời (attempt %s/%s), thử lại sau %.1fs: %s",
                    attempt + 1,
                    self.max_retries,
                    delay,
                    exc,
                )
                await self._sleep(delay)
        raise last_error or RuntimeError("BAPI request thất bại")

    async def _wait_for_cooldown(self) -> None:
        remaining = self._cooldown_until - time.monotonic()
        if remaining > 0:
            await self._sleep(remaining)

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise BapiError(
                response.status_code, "INVALID_JSON", "BAPI trả JSON không hợp lệ"
            ) from exc
        if not isinstance(payload, dict):
            raise BapiError(
                response.status_code, "INVALID_JSON", "BAPI trả payload không phải object"
            )
        return payload
