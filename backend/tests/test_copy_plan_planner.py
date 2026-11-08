from app.services.copy_plan.limits import DEFAULT_LIMITS
from app.services.copy_plan.planner import build_copy_plan
from app.services.copy_plan.validate import validate_plan


def _constraints(r: float | None = 100.0, a: float | None = 10.0) -> dict:
    return {
        "lead_portfolio_id": "1234567890",
        "fixed_radio_min_copy_usd": r,
        "fixed_amount_min_copy_usd": a,
        "profit_sharing_rate": 10.0,
        "current_copy_count": 5,
        "max_copy_count": 100,
    }


def _metrics(mdd: float | None = 20.0, worst: float | None = -35.0) -> dict:
    return {
        "mdd_90d": mdd,
        "worst_position_roi": worst,
        "max_leverage": 20.0,
        "avg_leverage": 8.0,
        "risk_level": "medium",
        "risk_score": 45.0,
    }


def _inputs(**kwargs) -> dict:
    data = {
        "trader_id": "1234567890",
        "capital_usd": 100.0,
        "risk_policy": "balanced",
    }
    data.update(kwargs)
    return data


def _symbols() -> dict:
    return {
        "top": [
            {"symbol": "BTCUSDT", "share_pct": 40.0},
            {"symbol": "XAUUSDT", "share_pct": 10.0},
        ],
        "tradfi": ["XAUUSDT"],
    }


def test_both_modes_auto_fixed_ratio() -> None:
    plan = build_copy_plan(_inputs(), _constraints(), _metrics())
    assert plan["copy_mode"]["value"] == "fixed_ratio"
    assert plan["copy_mode"]["status"] == "ok"
    assert plan["copy_mode"]["auto_selected"] is True
    assert plan["copy_mode"]["eligible_modes"] == ["fixed_ratio", "fixed_amount"]
    assert plan["can_copy"] is True
    assert plan["copy_amount_usd"]["value"] == 100.0


def test_preferred_ratio_eligible() -> None:
    plan = build_copy_plan(
        _inputs(preferred_mode="fixed_ratio"), _constraints(), _metrics()
    )
    assert plan["copy_mode"]["value"] == "fixed_ratio"
    assert plan["cost_per_order_usd"]["status"] == "inapplicable"
    assert plan["copy_amount_usd"]["value"] == 100.0


def test_preferred_ratio_invalid_falls_back_to_amount() -> None:
    plan = build_copy_plan(
        _inputs(capital_usd=50.0, preferred_mode="fixed_ratio"),
        _constraints(),
        _metrics(),
    )
    assert plan["copy_mode"]["value"] == "fixed_amount"
    assert plan["copy_mode"]["status"] == "ok"
    assert plan["copy_mode"]["auto_selected"] is True
    assert plan["can_copy"] is True
    assert any("tự chọn fixed_amount" in item for item in plan["warnings"])


def test_only_amount_mode_selects_automatically() -> None:
    plan = build_copy_plan(_inputs(capital_usd=50.0), _constraints(), _metrics())
    assert plan["copy_mode"]["value"] == "fixed_amount"
    assert plan["cost_per_order_usd"]["value"] == 10.0
    assert plan["cost_per_order_usd"]["status"] == "defaulted"


def test_capital_below_both_min_cannot_copy() -> None:
    plan = build_copy_plan(_inputs(capital_usd=5.0), _constraints(), _metrics())
    assert plan["copy_mode"]["status"] == "blocked"
    assert plan["can_copy"] is False


def test_available_below_capital_uses_available_and_blocks_ratio() -> None:
    plan = build_copy_plan(
        _inputs(available_usd=24.84),
        _constraints(),
        _metrics(),
        symbol_stats=_symbols(),
    )
    assert plan["copy_mode"]["value"] == "fixed_amount"
    assert plan["copy_amount_usd"]["value"] == 24.84
    assert plan["cost_per_order_usd"]["value"] == 10.0
    assert plan["max_cost_per_order_pct"]["value"] == 41
    assert any("lớn hơn khả dụng" in item for item in plan["warnings"])


def test_cost_per_order_above_min_is_not_defaulted() -> None:
    plan = build_copy_plan(
        _inputs(capital_usd=1000.0),
        _constraints(r=None, a=10.0),
        _metrics(),
    )
    assert plan["copy_mode"]["value"] == "fixed_amount"
    assert plan["cost_per_order_usd"]["value"] == 100.0
    assert plan["cost_per_order_usd"]["status"] == "ok"


def test_total_stop_loss_policies() -> None:
    safe = build_copy_plan(_inputs(risk_policy="safe"), _constraints(), _metrics())
    balanced = build_copy_plan(_inputs(risk_policy="balanced"), _constraints(), _metrics())
    aggressive = build_copy_plan(
        _inputs(risk_policy="aggressive"), _constraints(), _metrics()
    )
    assert safe["total_stop_loss_usd"]["value"] == 20.0
    assert balanced["total_stop_loss_usd"]["value"] == 30.0
    assert aggressive["total_stop_loss_usd"]["value"] == 43.75
    assert balanced["stop_loss_pct"]["value"] == 35


def test_total_stop_loss_falls_back_to_policy_cap() -> None:
    plan = build_copy_plan(
        _inputs(), _constraints(), _metrics(mdd=None, worst=None)
    )
    assert plan["total_stop_loss_usd"]["value"] == 30.0
    assert plan["total_stop_loss_usd"]["status"] == "defaulted"
    assert "total_stop_loss_usd" not in plan["missing_fields"]


def test_user_tp_sl_are_clamped() -> None:
    plan = build_copy_plan(
        _inputs(take_profit_pct=3000, stop_loss_pct=-5), _constraints(), _metrics()
    )
    assert plan["take_profit_pct"]["value"] == 2000
    assert plan["stop_loss_pct"]["value"] == 0
    assert any("vượt" in item or "ngoài biên" in item for item in plan["warnings"])


def test_custom_total_stop_loss_and_pct() -> None:
    plan = build_copy_plan(
        _inputs(
            risk_policy="custom",
            total_stop_loss_usd=12.5,
            max_cost_order_pct=7,
        ),
        _constraints(),
        _metrics(),
    )
    assert plan["total_stop_loss_usd"]["value"] == 12.5
    assert plan["max_cost_per_order_pct"]["value"] == 7


def test_symbol_scope_custom_and_unknown_warning() -> None:
    plan = build_copy_plan(
        _inputs(symbol_scope="custom", symbols=["BTCUSDT", "FOOUSDT"]),
        _constraints(),
        _metrics(),
        symbol_stats=_symbols(),
    )
    assert plan["symbols"]["value"] == ["BTCUSDT", "FOOUSDT"]
    assert any("FOOUSDT" in item for item in plan["warnings"])


def test_low_liquidity_missing() -> None:
    plan = build_copy_plan(
        _inputs(symbol_scope="exclude_low_liquidity"),
        _constraints(),
        _metrics(),
        symbol_stats=_symbols(),
    )
    assert plan["symbols"]["low_liquidity"] is None
    assert plan["symbols"]["status"] == "missing"
    assert "symbols.low_liquidity" in plan["missing_fields"]


def test_margin_and_leverage_copy_lead() -> None:
    plan = build_copy_plan(
        _inputs(),
        _constraints(),
        _metrics(),
        margin_mode={"mode": "isolated", "confidence": 0.8},
    )
    assert plan["margin_mode"]["value"] == "copy_lead"
    assert plan["margin_mode"]["lead_mode"] == "isolated"
    assert plan["leverage"]["value"] == "copy_lead"
    assert plan["leverage"]["lead_max"] == 20.0
    assert plan["leverage"]["effective"] is None


def test_advanced_defaults_are_auto_selected() -> None:
    plan = build_copy_plan(_inputs(), _constraints(), _metrics())
    expected = {
        "copy_existing_positions": False,
        "better_entry_price": True,
        "close_all_at_take_profit": False,
        "auto_invest": False,
    }
    for key, value in expected.items():
        assert plan[key]["value"] is value
        assert plan[key]["status"] == "defaulted"


def test_valid_plan_has_no_warnings() -> None:
    plan = build_copy_plan(
        _inputs(preferred_mode="fixed_ratio"),
        _constraints(),
        _metrics(),
        symbol_stats=_symbols(),
        margin_mode={"mode": "isolated", "confidence": 0.9},
    )
    plan["evidence_ids"] = [
        "1234567890:fixed_ratio_min_copy_usd",
        "1234567890:mdd_90d",
        "1234567890:worst_position_roi",
        "1234567890:max_leverage",
        "1234567890:margin_mode",
    ]
    facts = set(plan["evidence_ids"])
    assert validate_plan(plan, facts, DEFAULT_LIMITS) == []


def test_validate_flags_missing_evidence_and_bounds() -> None:
    plan = build_copy_plan(_inputs(), _constraints(), _metrics())
    warnings = validate_plan(plan, set(), DEFAULT_LIMITS)
    assert "copy_plan_evidence_unknown:1234567890:fixed_ratio_min_copy_usd" in warnings
    plan["copy_amount_usd"]["evidence_id"] = None
    assert "copy_plan_evidence_missing" in validate_plan(plan, set(), DEFAULT_LIMITS)
    plan["total_stop_loss_usd"]["value"] = 999
    assert "total_stop_loss_over_capital" in validate_plan(plan, None, DEFAULT_LIMITS)


def test_validate_flags_can_copy_below_min() -> None:
    plan = build_copy_plan(
        _inputs(preferred_mode="fixed_ratio"), _constraints(), _metrics()
    )
    plan["copy_amount_usd"]["value"] = 1
    warnings = validate_plan(plan, None, DEFAULT_LIMITS)
    assert "can_copy_true_below_mode_min" in warnings


def test_small_capital_plan_is_complete_no_questions() -> None:
    plan = build_copy_plan(
        _inputs(capital_usd=20.0, available_usd=20.0),
        _constraints(r=10.0, a=10.0),
        _metrics(mdd=40.0, worst=-179.6),
        symbol_stats={
            "top": [
                {"symbol": "1000PEPEUSDT", "share_pct": 73.67},
                {"symbol": "PUMPUSDT", "share_pct": 9.74},
            ],
            "tradfi": [],
        },
        margin_mode={"mode": "cross", "confidence": 1.0},
    )
    assert plan["copy_mode"]["value"] == "fixed_ratio"
    assert plan["can_copy"] is True
    assert plan["stop_loss_pct"]["value"] == 35
    assert plan["total_stop_loss_usd"]["value"] == 6.0
    assert plan["max_slippage_pct"]["value"] == 0.5
    assert plan["take_profit_pct"]["value"] is None
    assert plan["take_profit_pct"]["status"] == "defaulted"
    assert plan["auto_invest"]["value"] is False
    assert any("Tập trung cao" in item for item in plan["warnings"])
    assert plan["missing_fields"] == []
