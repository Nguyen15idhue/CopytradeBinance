"""Hàm thuần tạo copy_plan từ dữ liệu đã chuẩn hoá (kế hoạch 06 §5–§6)."""

import math
from typing import Any

from app.services.copy_plan.limits import DEFAULT_LIMITS, CopyLimits
from app.services.copy_plan.policy import RiskPolicy, compute_total_stop_loss, resolve_policy

PLAN_VERSION = 1


def _field(
    value: Any,
    source: str,
    status: str = "ok",
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"value": value, "source": source, "status": status}
    payload.update(extra)
    return payload


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _slot_available(constraints: dict[str, Any]) -> bool | None:
    current = constraints.get("current_copy_count")
    maximum = constraints.get("max_copy_count")
    if current is None or maximum is None:
        return None
    try:
        return int(current) < int(maximum)
    except (TypeError, ValueError):
        return None


def _trader_evidence(trader_id: str, key: str) -> str:
    return f"{trader_id}:{key}"


def build_copy_plan(
    inputs: dict[str, Any],
    constraints: dict[str, Any],
    metrics: dict[str, Any],
    symbol_stats: dict[str, Any] | None = None,
    margin_mode: dict[str, Any] | None = None,
    limits: CopyLimits | None = None,
) -> dict[str, Any]:
    """Tạo copy_plan tất định. Không đọc DB, không phụ thuộc LLM."""
    limits = limits or DEFAULT_LIMITS
    trader_id = str(inputs.get("trader_id") or constraints.get("lead_portfolio_id") or "")
    capital = _num(inputs.get("capital_usd"))
    if capital is None or capital <= 0:
        raise ValueError("capital_usd phải > 0")
    available = _num(inputs.get("available_usd"))
    if available is not None and available < 0:
        raise ValueError("available_usd phải >= 0")

    warnings: list[str] = []
    missing: list[str] = []
    assumptions: list[str] = []

    if available is not None and available < capital:
        warnings.append(
            f"Vốn khai báo {capital:.2f} USDT lớn hơn khả dụng {available:.2f} USDT; "
            f"dùng {available:.2f} USDT."
        )

    policy: RiskPolicy = resolve_policy(inputs.get("risk_policy"))
    assumptions.append(policy.note)

    r_min = _num(constraints.get("fixed_radio_min_copy_usd"))
    a_min = _num(constraints.get("fixed_amount_min_copy_usd"))
    profit_sharing = _num(constraints.get("profit_sharing_rate"))

    copy_max = max(limits.ratio_copy_max_usd, limits.amount_copy_max_usd)
    copy_upper = min(capital, copy_max)
    if available is not None:
        copy_upper = min(copy_upper, available)
    copy_upper = round(copy_upper, 2)

    ratio_ok = r_min is not None and copy_upper >= r_min
    amount_ok = a_min is not None and copy_upper >= a_min
    eligible_modes = [
        mode
        for mode, ok in (("fixed_ratio", ratio_ok), ("fixed_amount", amount_ok))
        if ok
    ]

    preferred = inputs.get("preferred_mode")
    if preferred not in (None, "fixed_ratio", "fixed_amount"):
        raise ValueError("preferred_mode không hợp lệ")
    blocked: list[dict[str, str]] = []
    mode: str | None
    mode_status = "ok"
    mode_note: str | None = None

    if r_min is None and a_min is None:
        mode = None
        mode_status = "missing"
        mode_note = "Không có dữ liệu min copy của trader."
        missing.append("copy_mode.min_copy")
        can_copy: bool | None = None
    elif preferred is not None:
        ok = ratio_ok if preferred == "fixed_ratio" else amount_ok
        if ok:
            mode = preferred
        else:
            mode = None
            mode_status = "blocked"
            mode_note = (
                f"Mode {preferred} không hợp lệ với số tiền copy {copy_upper:.2f} USDT."
            )
            blocked.append({"mode": preferred, "reason": mode_note})
            can_copy = False
    elif len(eligible_modes) == 1:
        mode = eligible_modes[0]
    elif len(eligible_modes) == 2:
        mode = None
        mode_status = "needs_choice"
        mode_note = "Cả hai mode đều hợp lệ; cần người dùng chọn."
    else:
        mode = None
        mode_status = "blocked"
        mode_note = "Không mode nào hợp lệ với số tiền copy hiện tại."
        can_copy = False

    if mode == "fixed_ratio":
        mode_min = r_min
        mode_max = limits.ratio_copy_max_usd
        copy_amount = round(min(copy_upper, mode_max), 2)
    elif mode == "fixed_amount":
        mode_min = a_min
        mode_max = limits.amount_copy_max_usd
        copy_amount = round(min(copy_upper, mode_max), 2)
    else:
        mode_min = min([item for item in (r_min, a_min) if item is not None], default=None)
        mode_max = copy_max
        copy_amount = copy_upper
    if mode is not None:
        can_copy = mode_min is not None and copy_amount >= mode_min
        if not can_copy:
            warnings.append(
                f"Số tiền copy {copy_amount:.2f} USDT nhỏ hơn min {mode_min} USDT của {mode}."
            )
    else:
        can_copy = can_copy if "can_copy" in locals() else (ratio_ok or amount_ok)

    if available is not None and copy_amount > available:
        copy_amount = round(available, 2)

    slot_available = _slot_available(constraints)
    if slot_available is False:
        can_copy = False
        warnings.append("Trader đã hết slot copy.")

    # --- chi phí mỗi lệnh -------------------------------------------------
    user_pct = _num(inputs.get("max_cost_order_pct"))
    pct = _clamp(
        user_pct if user_pct is not None else policy.max_cost_order_pct,
        limits.max_cost_order_pct_min,
        limits.max_cost_order_pct_max,
    )
    if user_pct is not None and user_pct != pct:
        warnings.append(
            f"max_cost_order_pct {user_pct} nằm ngoài biên "
            f"{limits.max_cost_order_pct_min:.0f}–{limits.max_cost_order_pct_max:.0f}%; "
            f"đã clamp về {pct:.0f}%."
        )

    cost_field: dict[str, Any]
    if mode == "fixed_amount":
        lower = max(a_min or 0.0, limits.amount_order_min_usd)
        upper = min(limits.amount_order_max_usd, copy_amount)
        if lower > upper:
            cost_field = _field(
                None, "computed", "infeasible",
                min=limits.amount_order_min_usd,
                max=limits.amount_order_max_usd,
                note="Không thể đạt lệnh tối thiểu trong giới hạn vốn.",
            )
            can_copy = False
            warnings.append(
                f"Chi phí mỗi lệnh tối thiểu {lower:.2f} USDT > số tiền copy {upper:.2f} USDT."
            )
        else:
            raw_cost = copy_amount * pct / 100
            cost = round(_clamp(raw_cost, lower, upper), 2)
            effective_pct = math.ceil(cost / copy_amount * 100) if copy_amount else 0
            if raw_cost < lower:
                pct = max(pct, float(effective_pct))
                warnings.append(
                    f"Lệnh tối thiểu {lower:.2f} USDT lớn hơn {pct:.0f}% của "
                    f"{copy_amount:.2f} USDT; nâng % chi phí tối đa lên {pct:.0f}%."
                )
            if pct > limits.max_cost_order_pct_max:
                cost_field = _field(
                    None, "computed", "infeasible",
                    min=limits.amount_order_min_usd,
                    max=limits.amount_order_max_usd,
                    note="% chi phí tối đa vượt biên 95%.",
                )
                can_copy = False
            else:
                cost_field = _field(
                    cost, "computed",
                    "defaulted" if raw_cost < lower else "ok",
                    unit="USDT",
                    min=limits.amount_order_min_usd,
                    max=limits.amount_order_max_usd,
                    evidence_id=_trader_evidence(trader_id, "fixed_amount_min_copy_usd"),
                    note="đã nâng để đạt lệnh tối thiểu" if raw_cost < lower else None,
                )
    else:
        cost_field = _field(
            None,
            "computed" if mode == "fixed_ratio" else "default",
            "inapplicable" if mode == "fixed_ratio" else "needs_choice",
            min=limits.amount_order_min_usd,
            max=limits.amount_order_max_usd,
            note="mode fixed_ratio không dùng chi phí mỗi lệnh"
            if mode == "fixed_ratio" else "cần chọn mode trước",
        )

    pct_field = _field(
        pct, "default", "defaulted", unit="%",
        min=limits.max_cost_order_pct_min,
        max=limits.max_cost_order_pct_max,
        note=f"theo chính sách {policy.name}",
    )

    # --- tổng cắt lỗ / TP / SL -------------------------------------------
    mdd = _num(metrics.get("mdd_90d"))
    worst_roi = _num(metrics.get("worst_position_roi"))
    mdd_loss = round(capital * mdd / 100, 2) if mdd is not None else None
    has_worst_loss = worst_roi is not None and worst_roi < 0
    worst_loss = round(capital * abs(worst_roi) / 100, 2) if has_worst_loss else None
    custom_total = _num(inputs.get("total_stop_loss_usd"))
    if policy.name == "custom" and custom_total is not None:
        total_sl = round(_clamp(custom_total, 0.01, capital), 2)
        if custom_total != total_sl:
            warnings.append("total_stop_loss_usd đã được clamp trong khoảng 0–capital.")
    else:
        total_sl = compute_total_stop_loss(capital, mdd_loss, worst_loss, policy)
    total_sl_cap = min(capital, copy_amount) if copy_amount > 0 else capital
    if total_sl is not None and total_sl > total_sl_cap:
        total_sl = round(total_sl_cap, 2)
    if total_sl is None:
        missing.append("total_stop_loss_usd")
        total_sl_field = _field(
            None, "missing", "missing", unit="USDT",
            note="Thiếu MDD 90D và worst position ROI.",
        )
    else:
        evidence_key = "worst_position_roi" if worst_loss is not None else "mdd_90d"
        total_sl_field = _field(
            total_sl, "computed", "ok", unit="USDT",
            evidence_id=_trader_evidence(trader_id, evidence_key),
        )

    user_sl = _num(inputs.get("stop_loss_pct"))
    if user_sl is not None:
        sl_pct = _clamp(user_sl, limits.sl_min_pct, limits.sl_max_pct)
        if sl_pct != user_sl:
            warnings.append(
                f"stop_loss_pct {user_sl} ngoài biên "
                f"{limits.sl_min_pct:.0f}–{limits.sl_max_pct:.0f}%; đã clamp."
            )
        sl_field = _field(sl_pct, "user", "ok", unit="%",
                          min=limits.sl_min_pct, max=limits.sl_max_pct)
    elif worst_roi is not None:
        sl_pct = _clamp(math.ceil(abs(worst_roi)), limits.sl_min_pct, limits.sl_max_pct)
        sl_field = _field(
            sl_pct, "computed", "ok", unit="%",
            min=limits.sl_min_pct, max=limits.sl_max_pct,
            evidence_id=_trader_evidence(trader_id, "worst_position_roi"),
            note="bằng mức lỗ lớn nhất đã quan sát",
        )
    else:
        missing.append("stop_loss_pct")
        sl_field = _field(None, "missing", "missing", unit="%",
                          min=limits.sl_min_pct, max=limits.sl_max_pct)

    user_tp = _num(inputs.get("take_profit_pct"))
    if user_tp is not None:
        tp_pct = _clamp(user_tp, limits.tp_min_pct, limits.tp_max_pct)
        if tp_pct != user_tp:
            warnings.append(
                f"take_profit_pct {user_tp} ngoài biên "
                f"{limits.tp_min_pct:.0f}–{limits.tp_max_pct:.0f}%; đã clamp."
            )
        tp_field = _field(tp_pct, "user", "ok", unit="%",
                          min=limits.tp_min_pct, max=limits.tp_max_pct)
    else:
        tp_field = _field(None, "default", "user_choice", unit="%",
                          min=limits.tp_min_pct, max=limits.tp_max_pct,
                          note="không có dữ liệu để suy; dùng mặc định Binance")

    # --- symbol / margin / leverage / advanced ---------------------------
    symbol_stats = symbol_stats or {}
    scope = str(inputs.get("symbol_scope") or "all")
    custom_symbols = [str(item) for item in (inputs.get("symbols") or [])]
    top_symbols = symbol_stats.get("top") or []
    tradfi = symbol_stats.get("tradfi") or []
    low_liquidity = symbol_stats.get("low_liquidity")
    allow_tradfi = inputs.get("allow_tradfi")
    if scope not in ("all", "exclude_low_liquidity", "custom"):
        raise ValueError("symbol_scope không hợp lệ")
    if scope == "custom" and custom_symbols:
        known = {item.get("symbol") for item in top_symbols if isinstance(item, dict)}
        unknown = [item for item in custom_symbols if known and item not in known]
        if unknown:
            warnings.append(
                "Symbol không có trong lịch sử giao dịch của lead: " + ", ".join(unknown)
            )
        symbols_field = _field(custom_symbols, "user", "ok", mode="custom",
                               note="danh sách người dùng nhập")
    elif scope == "all":
        symbols_field = _field(None, "default", "user_choice", mode="all",
                               note="copy toàn bộ symbol")
    else:
        symbols_field = _field(None, "missing", "missing", mode=scope,
                               note="chưa có volume 24h để lọc thanh khoản thấp")
        missing.append("symbols.low_liquidity")
    symbols_block: dict[str, Any] = {
        **symbols_field,
        "tradfi": tradfi,
        "low_liquidity": low_liquidity,
        "top": top_symbols,
    }
    if allow_tradfi is not None:
        symbols_block["tradfi_allowed"] = bool(allow_tradfi)
        if not allow_tradfi and tradfi:
            warnings.append(
                "Đã tắt TradFi nhưng lead có giao dịch cặp TradFi: " + ", ".join(tradfi)
            )
    if low_liquidity is None and "symbols.low_liquidity" not in missing:
        missing.append("symbols.low_liquidity")

    if margin_mode and margin_mode.get("mode"):
        margin_field = _field(
            "copy_lead", "derived", "ok",
            lead_mode=margin_mode.get("mode"),
            confidence=margin_mode.get("confidence"),
            evidence_id=_trader_evidence(trader_id, "margin_mode"),
        )
    else:
        missing.append("margin_mode.lead_mode")
        margin_field = _field(
            None, "missing", "missing",
            note="Không có position để suy margin mode của lead.",
        )

    lead_max = _num(metrics.get("max_leverage"))
    lead_avg = _num(metrics.get("avg_leverage"))
    leverage_field = _field(
        "copy_lead", "derived" if lead_max is not None else "default", "ok",
        lead_max=lead_max,
        lead_avg=lead_avg,
        effective=None,
        evidence_id=_trader_evidence(trader_id, "max_leverage") if lead_max is not None else None,
        note="Binance tính đòn bẩy hiệu lực; plan chỉ hiển thị đòn bẩy lead.",
    )
    if lead_max is None:
        missing.append("leverage.lead_stats")

    user_slippage = _num(inputs.get("max_slippage_pct"))
    if user_slippage is not None:
        slippage_field = _field(user_slippage, "user", "ok", unit="%")
    else:
        missing.append("max_slippage_pct")
        slippage_field = _field(
            None, "missing", "missing", unit="%",
            note="hệ thống không có dữ liệu slippage; dùng mặc định Binance",
        )

    advanced: dict[str, dict[str, Any]] = {}
    for key in (
        "copy_existing_positions",
        "better_entry_price",
        "close_all_at_take_profit",
        "auto_invest",
    ):
        value = inputs.get(key)
        if value is None:
            advanced[key] = _field(None, "default", "user_choice")
        else:
            advanced[key] = _field(bool(value), "user", "ok")

    if mode_min is not None:
        copy_field = _field(
            copy_amount, "computed", "ok", unit="USDT",
            min=mode_min, max=mode_max,
            max_available=available,
            evidence_id=_trader_evidence(
                trader_id,
                "fixed_ratio_min_copy_usd" if mode == "fixed_ratio"
                else "fixed_amount_min_copy_usd",
            ) if mode is not None else None,
        )
    else:
        copy_field = _field(
            copy_amount, "computed", "missing", unit="USDT",
            min=None, max=mode_max, max_available=available,
            note="thiếu min copy của trader",
        )

    mode_field = _field(
        mode, "computed", mode_status,
        eligible_modes=eligible_modes,
        blocked_modes=blocked,
        note=mode_note,
    )

    plan: dict[str, Any] = {
        "version": PLAN_VERSION,
        "trader_id": trader_id,
        "limits_version": limits.version,
        "inputs": {
            "capital_usd": capital,
            "available_usd": available,
            "risk_policy": policy.name,
            "preferred_mode": preferred,
        },
        "copy_mode": mode_field,
        "copy_amount_usd": copy_field,
        "cost_per_order_usd": cost_field,
        "max_cost_per_order_pct": pct_field,
        "total_stop_loss_usd": total_sl_field,
        "symbols": symbols_block,
        "copy_existing_positions": advanced["copy_existing_positions"],
        "better_entry_price": advanced["better_entry_price"],
        "margin_mode": margin_field,
        "leverage": leverage_field,
        "max_slippage_pct": slippage_field,
        "take_profit_pct": tp_field,
        "stop_loss_pct": sl_field,
        "close_all_at_take_profit": advanced["close_all_at_take_profit"],
        "auto_invest": advanced["auto_invest"],
        "can_copy": can_copy,
        "used_capital_usd": copy_amount if copy_amount > 0 else None,
        "profit_sharing_rate": profit_sharing,
        "slot_available": slot_available,
        "warnings": warnings,
        "missing_fields": list(dict.fromkeys(missing)),
        "assumptions": assumptions,
        "evidence_ids": [],
    }
    return plan
