"""Đánh dấu log do test tạo để scheduler không dùng làm last_success."""

import os


def is_test_run() -> bool:
    return bool(os.getenv("PYTEST_CURRENT_TEST"))


def test_detail(detail: dict | None = None) -> dict:
    payload = dict(detail or {})
    if is_test_run():
        payload["test"] = True
    return payload
