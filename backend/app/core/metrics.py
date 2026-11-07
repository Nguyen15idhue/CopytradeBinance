"""Bộ đếm Prometheus tối giản trong process."""

import time
from collections import defaultdict

REQUEST_COUNT: dict[tuple[str, str, int], int] = defaultdict(int)
REQUEST_DURATION_SUM: dict[tuple[str, str], float] = defaultdict(float)
STARTED_AT = time.time()


def observe(method: str, path: str, status: int, duration: float) -> None:
    REQUEST_COUNT[(method, path, status)] += 1
    REQUEST_DURATION_SUM[(method, path)] += duration


def render() -> str:
    lines = [
        "# HELP http_requests_total Tổng request theo method/path/status.",
        "# TYPE http_requests_total counter",
    ]
    for (method, path, status), count in sorted(REQUEST_COUNT.items()):
        lines.append(
            f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
        )
    lines += [
        "# HELP http_request_duration_seconds_sum Tổng thời gian xử lý.",
        "# TYPE http_request_duration_seconds_sum counter",
    ]
    for (method, path), total in sorted(REQUEST_DURATION_SUM.items()):
        lines.append(
            f'http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total:.6f}'
        )
    lines.append(f"process_uptime_seconds {time.time() - STARTED_AT:.1f}")
    return "\n".join(lines) + "\n"
