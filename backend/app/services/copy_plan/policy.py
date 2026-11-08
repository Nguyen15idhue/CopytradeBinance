"""Chính sách rủi ro cho copy plan (hằng số sản phẩm, không phải dữ liệu)."""

import math
from dataclasses import dataclass
from typing import Literal

LossMode = Literal["mdd", "max_observed", "max_observed_125"]


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    name: str
    max_cost_order_pct: float
    loss_mode: LossMode
    stop_loss_cap_pct: float
    total_stop_loss_cap_pct: float
    max_slippage_pct: float
    note: str


POLICIES: dict[str, RiskPolicy] = {
    "safe": RiskPolicy(
        "safe", 5.0, "mdd", 20.0, 0.20, 0.3,
        "safe: max cost/order 5%, SL tối đa 20%, tổng cắt lỗ tối đa 20% vốn, "
        "slippage 0.3%.",
    ),
    "balanced": RiskPolicy(
        "balanced", 10.0, "max_observed", 35.0, 0.30, 0.5,
        "balanced: max cost/order 10%, SL tối đa 35%, tổng cắt lỗ tối đa 30% vốn, "
        "slippage 0.5%.",
    ),
    "aggressive": RiskPolicy(
        "aggressive", 20.0, "max_observed_125", 50.0, 0.50, 1.0,
        "aggressive: max cost/order 20%, SL tối đa 50%, tổng cắt lỗ tối đa 50% vốn, "
        "slippage 1%.",
    ),
    "custom": RiskPolicy(
        "custom", 10.0, "max_observed", 35.0, 0.30, 0.5,
        "custom: người dùng tự nhập max cost/order, SL và tổng cắt lỗ.",
    ),
}


def resolve_policy(name: str | None) -> RiskPolicy:
    """Trả policy hợp lệ; tên lạ fallback balanced (không ném lỗi)."""
    return POLICIES.get((name or "balanced").lower(), POLICIES["balanced"])


def compute_total_stop_loss(
    capital_usd: float,
    mdd_loss_usd: float | None,
    worst_loss_usd: float | None,
    policy: RiskPolicy,
) -> float:
    """Tổng cắt lỗ tham chiếu, luôn có giá trị theo cap của policy."""
    if policy.loss_mode == "mdd":
        value = mdd_loss_usd
    else:
        candidates = [item for item in (mdd_loss_usd, worst_loss_usd) if item is not None]
        value = max(candidates) if candidates else None
        if value is not None and policy.loss_mode == "max_observed_125":
            value = value * 1.25
    cap = capital_usd * policy.total_stop_loss_cap_pct
    if value is None:
        return round(cap, 2)
    return round(min(cap, value), 2)


def compute_stop_loss_pct(worst_position_roi: float | None, policy: RiskPolicy) -> float:
    """SL vị thế: theo mức lỗ lớn nhất đã quan sát nhưng không vượt cap policy."""
    if worst_position_roi is None:
        return policy.stop_loss_cap_pct
    return round(min(math.ceil(abs(worst_position_roi)), policy.stop_loss_cap_pct), 2)
