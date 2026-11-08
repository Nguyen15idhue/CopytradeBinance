"""Chính sách rủi ro cho copy plan (hằng số sản phẩm, không phải dữ liệu)."""

from dataclasses import dataclass
from typing import Literal

LossMode = Literal["mdd", "max_observed", "max_observed_125"]


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    name: str
    max_cost_order_pct: float
    loss_mode: LossMode
    note: str


POLICIES: dict[str, RiskPolicy] = {
    "safe": RiskPolicy(
        "safe", 5.0, "mdd",
        "safe: max cost/order 5%, tổng cắt lỗ theo MDD 90D.",
    ),
    "balanced": RiskPolicy(
        "balanced", 10.0, "max_observed",
        "balanced: max cost/order 10%, tổng cắt lỗ theo mức lỗ lớn hơn "
        "giữa MDD và worst position.",
    ),
    "aggressive": RiskPolicy(
        "aggressive", 20.0, "max_observed_125",
        "aggressive: max cost/order 20%, tổng cắt lỗ theo mức lỗ lớn hơn "
        "giữa MDD và worst position, nhân 1.25.",
    ),
    "custom": RiskPolicy(
        "custom", 10.0, "max_observed",
        "custom: người dùng tự nhập max cost/order và tổng cắt lỗ.",
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
) -> float | None:
    """Tổng cắt lỗ tham chiếu; None nếu không có dữ liệu MDD/worst."""
    if policy.loss_mode == "mdd":
        value = mdd_loss_usd
    else:
        candidates = [item for item in (mdd_loss_usd, worst_loss_usd) if item is not None]
        value = max(candidates) if candidates else None
        if value is not None and policy.loss_mode == "max_observed_125":
            value = value * 1.25
    if value is None:
        return None
    return round(min(capital_usd, value), 2)
