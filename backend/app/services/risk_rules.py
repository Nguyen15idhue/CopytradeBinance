"""Risk rules R01–R19 + risk_score V2. Không tự loại trader; chỉ event + evidence."""

from typing import Any

SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low_sample": 1,
    "confidence_penalty": 1,
    "insufficient": 1,
    "unknown": 0,
}

LEVEL_ALIAS = {
    "low_sample": "low",
    "confidence_penalty": "low",
    "insufficient": "low",
}

LEVEL_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0, "unknown": 0}

RULES = {
    "R01": ("runtime_days", "insufficient", 30, "lt", "Runtime < 30 ngày"),
    "R02": ("mdd_90d", "high", 20, "gt", "MDD > 20%"),
    "R03": ("mdd_90d", "critical", 30, "gt", "MDD > 30%"),
    "R04": ("max_leverage", "high", 10, "gt", "Max leverage > 10x"),
    "R05": ("max_leverage", "critical", 20, "gt", "Max leverage > 20x"),
    "R06": ("worst_position_roi", "critical", -80, "le", "Vị thế đã đóng lỗ ≤ −80%"),
    "R07": ("total_orders_90d", "low_sample", 20, "lt", "totalOrder < 20"),
    "R08": ("sharpe_90d", "confidence_penalty", None, "null", "Sharpe null"),
    "R09": ("freshness_minutes", "medium", 150, "gt", "Dữ liệu cũ > 150 phút"),
    "R10": ("copier_vs_lead", "high", 0, "copier_negative", "Copier PnL âm, lead dương"),
    "R11": ("copy_aum_ratio", "medium", 5, "lt", "Copy AUM < 5% AUM"),
    "R12": ("fee_drag_pct", "medium", 20, "gt", "Fee drag > 20%"),
    "R13": ("concentration", "medium", None, "concentrated", "Tập trung cao"),
    "R14": ("near_liquidation_count", "high", 1, "ge", "Vị thế lỗ sâu (−50% đến −80%)"),
    "R15": ("profit_quality", "medium", 1, "profit_weak", "Profit factor < 1"),
    "R16": ("calmar", "high", 0, "lt", "Calmar < 0"),
    "R17": ("confidence_value", "medium", 0.5, "lt", "Confidence < 0.5"),
    "R18": ("sharpe_90d", "high", 0, "sharpe_negative", "Sharpe âm"),
    "R19": ("sharpe_90d", "medium", 0.5, "sharpe_low", "Sharpe thấp (< 0.5)"),
}


def _value(metrics: dict[str, Any], field: str) -> Any:
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    if field == "mdd_90d":
        return published.get("mdd")
    if field == "total_orders_90d":
        return published.get("total_orders")
    if field == "sharpe_90d":
        return published.get("sharpe")
    if field == "copier_vs_lead":
        return {"copier_pnl": published.get("copier_pnl"), "pnl": published.get("pnl")}
    if field == "copy_aum_ratio":
        return derived.get("copy_aum_ratio")
    if field == "worst_position_roi":
        return derived.get("worst_position_roi")
    if field == "max_leverage":
        return derived.get("max_leverage")
    if field == "fee_drag_pct":
        return derived.get("fee_drag_pct")
    if field == "concentration":
        return {"hhi": derived.get("hhi"), "top_share": derived.get("top_symbol_share")}
    if field == "near_liquidation_count":
        return derived.get("near_liquidation_count")
    if field == "profit_quality":
        return {
            "profit_factor": derived.get("profit_factor"),
            "positions": derived.get("positions_count"),
        }
    if field == "calmar":
        return derived.get("calmar")
    if field == "confidence_value":
        return (metrics.get("confidence") or {}).get("value")
    return metrics.get(field)


def _triggered(
    rule_id: str, field: str, severity: str, threshold: Any, op: str, value: Any
) -> bool | None:
    if op == "null":
        return value is None
    if field == "copier_vs_lead":
        if (
            not isinstance(value, dict)
            or value.get("copier_pnl") is None
            or value.get("pnl") is None
        ):
            return None
        return value["copier_pnl"] < 0 < value["pnl"]
    if op == "sharpe_negative":
        if value is None:
            return None
        return float(value) < 0
    if op == "sharpe_low":
        if value is None:
            return None
        number = float(value)
        return 0 <= number < float(threshold)
    if op == "concentrated":
        if not isinstance(value, dict):
            return None
        hhi = value.get("hhi")
        top = value.get("top_share")
        if hhi is None and top is None:
            return None
        return (hhi is not None and float(hhi) > 0.4) or (
            top is not None and float(top) > 50
        )
    if op == "profit_weak":
        if not isinstance(value, dict):
            return None
        positions = value.get("positions")
        factor = value.get("profit_factor")
        if positions is None or int(positions) < 5:
            return None
        if factor is None:
            return None
        return float(factor) < 1
    if op == "ge":
        if value is None:
            return None
        return float(value) >= float(threshold)
    if value is None:
        return None
    value = float(value)
    if op == "gt":
        return value > float(threshold)
    if op == "lt":
        return value < float(threshold)
    if op == "le":
        return value <= float(threshold)
    return None


def _lerp(value: float, anchors: list[tuple[float, float]]) -> float:
    if value <= anchors[0][0]:
        return anchors[0][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:], strict=False):
        if value <= x1:
            ratio = (value - x0) / (x1 - x0) if x1 > x0 else 0.0
            return y0 + ratio * (y1 - y0)
    return anchors[-1][1]


def norm_mdd(value: float | None) -> float | None:
    if value is None:
        return None
    return round(_lerp(float(value), [(10, 0), (15, 25), (20, 50), (30, 80), (40, 100)]), 2)


def norm_leverage(value: float | None) -> float | None:
    if value is None:
        return None
    return round(_lerp(float(value), [(3, 0), (5, 30), (10, 70), (20, 100)]), 2)


def norm_sharpe(value: float | None) -> float:
    if value is None:
        return 70.0
    number = float(value)
    if number >= 1.5:
        return 0.0
    if number >= 1.0:
        return 20.0
    if number >= 0.5:
        return 50.0
    if number >= 0:
        return 75.0
    return 100.0


def norm_concentration(derived: dict[str, Any]) -> float | None:
    parts: list[float] = []
    hhi = derived.get("hhi")
    top = derived.get("top_symbol_share")
    worst = derived.get("worst_position_roi")
    fee = derived.get("fee_drag_pct")
    if hhi is not None:
        parts.append(_lerp(float(hhi), [(0.2, 0), (0.4, 50), (0.6, 80), (0.8, 100)]))
    if top is not None:
        parts.append(_lerp(float(top), [(20, 0), (50, 70), (80, 100)]))
    if worst is not None:
        number = float(worst)
        if number > -20:
            parts.append(0.0)
        else:
            parts.append(_lerp(number, [(-100, 100), (-80, 90), (-50, 50), (-20, 0)]))
    if fee is not None:
        number = float(fee)
        parts.append(0.0 if number < 0 else _lerp(number, [(5, 0), (20, 70), (50, 100)]))
    if not parts:
        return None
    return round(max(parts), 2)


def norm_quality(metrics: dict[str, Any]) -> float | None:
    parts: list[float] = []
    runtime = metrics.get("runtime_days")
    published = (metrics.get("published") or {}).get("90D", {})
    freshness = metrics.get("freshness_minutes")
    confidence = (metrics.get("confidence") or {}).get("value")
    if runtime is not None:
        number = float(runtime)
        if number < 30:
            parts.append(100.0)
        elif number < 90:
            parts.append(60.0)
        elif number < 180:
            parts.append(30.0)
        else:
            parts.append(0.0)
    orders = published.get("total_orders")
    if orders is not None:
        number = int(orders)
        parts.append(80.0 if number < 20 else (40.0 if number < 50 else 0.0))
    if freshness is not None:
        parts.append(70.0 if float(freshness) > 150 else 0.0)
    if confidence is not None:
        number = float(confidence)
        parts.append(80.0 if number < 0.5 else (30.0 if number < 0.8 else 0.0))
    if not parts:
        return None
    return round(max(parts), 2)


def norm_copy(metrics: dict[str, Any]) -> float | None:
    derived = metrics.get("derived") or {}
    published = (metrics.get("published") or {}).get("90D", {})
    parts: list[float] = []
    ratio = derived.get("copy_aum_ratio")
    if ratio is not None:
        number = float(ratio)
        if number < 1:
            parts.append(90.0)
        elif number < 5:
            parts.append(70.0)
        elif number < 20:
            parts.append(30.0)
        else:
            parts.append(0.0)
    copier = published.get("copier_pnl")
    pnl = published.get("pnl")
    if copier is not None and pnl is not None and float(copier) < 0 < float(pnl):
        parts.append(100.0)
    if not parts:
        return None
    return round(max(parts), 2)


def compute_risk_score(metrics: dict[str, Any]) -> dict[str, Any]:
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    if published.get("mdd") is None and derived.get("max_leverage") is None:
        return {"score": None, "components": {
            "mdd": None, "leverage": None, "sharpe": norm_sharpe(published.get("sharpe")),
            "concentration": norm_concentration(derived),
            "quality": norm_quality(metrics), "copy": norm_copy(metrics),
        }}
    components: dict[str, float | None] = {
        "mdd": norm_mdd(published.get("mdd")),
        "leverage": norm_leverage(derived.get("max_leverage")),
        "sharpe": norm_sharpe(published.get("sharpe")),
        "concentration": norm_concentration(derived),
        "quality": norm_quality(metrics),
        "copy": norm_copy(metrics),
    }
    weights = {"mdd": 30, "leverage": 20, "sharpe": 15,
               "concentration": 15, "quality": 10, "copy": 10}
    present = {key: value for key, value in components.items() if value is not None}
    if not present:
        return {"score": None, "components": components}
    total = sum(weights[key] for key in present)
    score = sum(present[key] * weights[key] for key in present) / total
    return {"score": round(score, 2), "components": components}


def score_to_level(score: float | None) -> str | None:
    if score is None:
        return None
    if score <= 20:
        return "none"
    if score <= 40:
        return "low"
    if score <= 60:
        return "medium"
    if score <= 80:
        return "high"
    return "critical"


def eligible_for_low_risk(metrics: dict[str, Any]) -> bool:
    published = (metrics.get("published") or {}).get("90D", {})
    derived = metrics.get("derived") or {}
    sharpe = published.get("sharpe")
    if sharpe is None or float(sharpe) < 0:
        return False
    if 0 <= float(sharpe) < 0.5:
        mdd = published.get("mdd")
        lev = derived.get("max_leverage")
        runtime = metrics.get("runtime_days")
        if mdd is None or lev is None or runtime is None:
            return False
        return (
            float(mdd) <= 15 and float(lev) <= 3 and float(runtime) >= 180
        )
    return True


def evaluate_rules(metrics: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    unknown: list[str] = []
    for rule_id, (field, severity, threshold, op, label) in RULES.items():
        value = _value(metrics, field)
        result = _triggered(rule_id, field, severity, threshold, op, value)
        if result is None:
            unknown.append(rule_id)
            continue
        if not result:
            continue
        evidence = {"field": field, "value": value, "threshold": threshold, "rule": rule_id}
        if field == "copier_vs_lead":
            evidence = {"field": "copier_pnl/pnl", "value": value,
                        "threshold": 0, "rule": rule_id}
        if field == "profit_quality":
            evidence = {"field": "profit_factor/positions", "value": value,
                        "threshold": 1, "rule": rule_id}
        if field == "concentration":
            evidence = {"field": "hhi/top_share", "value": value,
                        "threshold": "hhi>0.4|top>50", "rule": rule_id}
        events.append(
            {"code": rule_id, "severity": severity, "label": label, "evidence": evidence}
        )
    scored = compute_risk_score(metrics)
    event_level = risk_level(events, unknown)
    score_level = score_to_level(scored["score"])
    final = event_level
    if score_level is not None and LEVEL_ORDER.get(score_level, 0) > LEVEL_ORDER.get(
        final, 0
    ):
        # unknown (0) không kéo tụt event level; chỉ nâng khi score xấu hơn
        if not (final == "unknown" and score_level in ("none", "low")):
            final = score_level
        elif final == "unknown" and score_level in ("medium", "high", "critical"):
            final = score_level
    veto = sorted({event["code"] for event in events if event["code"] in
                   {"R02", "R03", "R04", "R05", "R06", "R14", "R18", "R19"}})
    return {
        "events": events,
        "unknown": unknown,
        "risk_level": final,
        "risk_score": scored["score"],
        "risk_components": scored["components"],
        "veto_reasons": veto,
        "low_risk_eligible": eligible_for_low_risk(metrics),
    }


def risk_level(events: list[dict[str, Any]], unknown: list[str]) -> str:
    if not events:
        return "unknown" if unknown else "none"
    top = max(
        (event["severity"] for event in events),
        key=lambda item: SEVERITY_ORDER.get(item, 0),
    )
    return LEVEL_ALIAS.get(top, top)
