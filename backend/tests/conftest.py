import os

import pytest

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_login_rate_limit():
    """Test integration đăng nhập nhiều lần; reset bộ đếm để không dính 429."""
    if os.getenv("RUN_INTEGRATION") == "1":
        try:
            limiter.reset()
        except Exception:  # noqa: BLE001 - storage có thể không hỗ trợ reset
            pass
        try:
            from app.main import API_HITS

            API_HITS.clear()
        except Exception:  # noqa: BLE001
            pass
    yield
