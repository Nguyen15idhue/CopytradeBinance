from app.services.ranking import select_boards
from app.services.risk_rules import compute_risk_score, eligible_for_low_risk, evaluate_rules


def _metrics(**overrides):
    base = {
        "runtime_days": 120,
        "freshness_minutes": 30,
        "confidence": {"value": 0.85},
        "published": {
            "90D": {
                "mdd": 10.0,
                "total_orders": 100,
                "sharpe": 1.2,
                "copier_pnl": 10.0,
                "pnl": 100.0,
                "roi": 20.0,
            }
        },
        "derived": {
            "max_leverage": 4.0,
            "worst_position_roi": -20.0,
            "copy_aum_ratio": 40.0,
            "fee_drag_pct": 2.0,
            "hhi": 0.15,
            "top_symbol_share": 25.0,
            "near_liquidation_count": 0,
            "profit_factor": 1.5,
            "positions_count": 20,
            "calmar": 2.0,
        },
    }
    for key, value in overrides.items():
        if key in {"published", "derived", "confidence"}:
            base[key] = value
        elif key.startswith("p_"):
            base["published"]["90D"][key[2:]] = value
        elif key.startswith("d_"):
            base["derived"][key[2:]] = value
        else:
            base[key] = value
    return base


def test_sharpe_negative_forces_high_and_bans_low_risk() -> None:
    result = evaluate_rules(_metrics(p_sharpe=-0.4))
    assert "R18" in {event["code"] for event in result["events"]}
    assert result["risk_level"] == "high"
    assert result["low_risk_eligible"] is False
    assert result["risk_score"] is not None and result["risk_score"] > 0


def test_sharpe_low_bans_low_risk_without_exception() -> None:
    result = evaluate_rules(_metrics(p_sharpe=0.3))
    assert "R19" in {event["code"] for event in result["events"]}
    assert result["risk_level"] in ("medium", "high")
    assert result["low_risk_eligible"] is False


def test_sharpe_low_exception_allows_low_risk() -> None:
    metrics = _metrics(p_sharpe=0.3, p_mdd=12.0, d_max_leverage=3.0)
    metrics["runtime_days"] = 200
    assert eligible_for_low_risk(metrics) is True


def test_fee_rebate_negative_does_not_trigger() -> None:
    result = evaluate_rules(_metrics(d_fee_drag_pct=-5.0))
    assert "R12" not in {event["code"] for event in result["events"]}


def test_fee_drag_high_triggers() -> None:
    result = evaluate_rules(_metrics(d_fee_drag_pct=25.0))
    assert "R12" in {event["code"] for event in result["events"]}


def test_profit_factor_small_sample_is_unknown() -> None:
    metrics = _metrics(d_profit_factor=0.5, d_positions_count=3)
    result = evaluate_rules(metrics)
    assert "R15" not in {event["code"] for event in result["events"]}
    assert "R15" in result["unknown"]


def test_low_risk_board_excludes_sharpe_negative() -> None:
    good = {
        "id": "a", "nickname": "A", "tier": "qualified", "score": 90.0,
        "band": "good", "confidence": 0.85, "risk_level": "high",
        "roi_90d": 20.0, "mdd_90d": 12.0, "sharpe": -0.4,
        "max_leverage": 4.0, "runtime_days": 120,
        "consistency_score": 80.0, "rankable": True,
    }
    boards = select_boards([good])
    assert boards["low_risk"] == []
    assert len(boards["overall"]) == 1


def test_risk_score_renormalizes_when_missing() -> None:
    scored = compute_risk_score({
        "published": {"90D": {"sharpe": 1.2, "mdd": 12.0}},
        "derived": {},
    })
    assert scored["score"] is not None


def test_risk_score_none_when_no_loss_data() -> None:
    scored = compute_risk_score({"published": {"90D": {"sharpe": 1.2}}, "derived": {}})
    assert scored["score"] is None
