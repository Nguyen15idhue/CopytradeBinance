"""Giới hạn form copy trading Binance (phiên bản hoá).

Nguồn: form thiết lập copy phía copier, ghi nhận 2026-11.
Binance dùng tên raw ``fixedRadioMinCopyUsd`` (thiếu chữ "t"); code giữ đúng
tên nguồn, không tự sửa thành ``fixedRatio``.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

COPY_LIMITS_VERSION = "2026-11-binance-copy-form-v1"


@dataclass(frozen=True, slots=True)
class CopyLimits:
    """Các biên của form copy trading, không phải dữ liệu thị trường."""

    ratio_copy_min_usd: float = 10.0
    ratio_copy_max_usd: float = 300_000.0
    amount_order_min_usd: float = 10.0
    amount_order_max_usd: float = 50_000.0
    amount_copy_min_usd: float = 10.0
    amount_copy_max_usd: float = 300_000.0
    tp_min_pct: float = 0.0
    tp_max_pct: float = 2_000.0
    sl_min_pct: float = 0.0
    sl_max_pct: float = 95.0
    max_cost_order_pct_min: float = 5.0
    max_cost_order_pct_max: float = 95.0
    version: str = COPY_LIMITS_VERSION


def limits_from_settings(settings: "Settings") -> CopyLimits:
    """Tạo CopyLimits từ Settings để có thể override bằng biến môi trường."""
    return CopyLimits(
        ratio_copy_min_usd=settings.copy_ratio_min_usd,
        ratio_copy_max_usd=settings.copy_ratio_max_usd,
        amount_order_min_usd=settings.copy_amount_order_min_usd,
        amount_order_max_usd=settings.copy_amount_order_max_usd,
        amount_copy_min_usd=settings.copy_amount_copy_min_usd,
        amount_copy_max_usd=settings.copy_amount_copy_max_usd,
        tp_min_pct=settings.copy_tp_min_pct,
        tp_max_pct=settings.copy_tp_max_pct,
        sl_min_pct=settings.copy_sl_min_pct,
        sl_max_pct=settings.copy_sl_max_pct,
        max_cost_order_pct_min=settings.copy_max_cost_order_pct_min,
        max_cost_order_pct_max=settings.copy_max_cost_order_pct_max,
        version=settings.copy_limits_version,
    )


DEFAULT_LIMITS = CopyLimits()
