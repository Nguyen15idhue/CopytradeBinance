from app.services.risk_rules import evaluate_rules


def _metrics(**overrides):
    base = {
        "runtime_days": 120,
        "freshness_minutes": 30,
        "published": {
            "90D": {
                "mdd": 10.0,
                "total_orders": 100,
                "sharpe": 1.2,
                "copier_pnl": 10.0,
                "pnl": 100.0,
            }
        },
        "derived": {
            "max_leverage": 5.0,
            "worst_position_roi": -20.0,
            "copy_aum_ratio": 40.0,
        },
    }
    for key, value in overrides.items():
        if key in {"published", "derived"}:
            base[key] = value
        elif key.startswith("p_"):
            base["published"]["90D"][key[2:]] = value
        elif key.startswith("d_"):
            base["derived"][key[2:]] = value
        else:
            base[key] = value
    return base


def test_clean_trader_has_no_events() -> None:
    result = evaluate_rules(_metrics())
    assert result["events"] == []
    assert result["risk_level"] == "none"


def test_r01_low_runtime() -> None:
    result = evaluate_rules(_metrics(runtime_days=10))
    assert {event["code"] for event in result["events"]} == {"R01"}
    assert result["risk_level"] == "low"


def test_r02_r03_mdd_levels() -> None:
    high = evaluate_rules(_metrics(p_mdd=25))
    assert {event["code"] for event in high["events"]} == {"R02"}
    assert high["risk_level"] == "high"
    critical = evaluate_rules(_metrics(p_mdd=35))
    assert {"R02", "R03"} <= {event["code"] for event in critical["events"]}
    assert critical["risk_level"] == "critical"


def test_r04_r05_leverage_levels() -> None:
    high = evaluate_rules(_metrics(d_max_leverage=15))
    assert {event["code"] for event in high["events"]} == {"R04"}
    critical = evaluate_rules(_metrics(d_max_leverage=25))
    assert {"R04", "R05"} <= {event["code"] for event in critical["events"]}


def test_r06_worst_position() -> None:
    result = evaluate_rules(_metrics(d_worst_position_roi=-85))
    assert {event["code"] for event in result["events"]} == {"R06"}
    assert result["events"][0]["evidence"]["value"] == -85


def test_r07_low_sample() -> None:
    result = evaluate_rules(_metrics(p_total_orders=10))
    assert {event["code"] for event in result["events"]} == {"R07"}


def test_r08_missing_sharpe() -> None:
    result = evaluate_rules(_metrics(p_sharpe=None))
    assert {event["code"] for event in result["events"]} == {"R08"}


def test_r09_stale_data() -> None:
    result = evaluate_rules(_metrics(freshness_minutes=200))
    assert {event["code"] for event in result["events"]} == {"R09"}


def test_r10_copier_loses_while_lead_wins() -> None:
    result = evaluate_rules(_metrics(p_copier_pnl=-5))
    assert {event["code"] for event in result["events"]} == {"R10"}


def test_r11_small_copy_aum() -> None:
    result = evaluate_rules(_metrics(d_copy_aum_ratio=2))
    assert {event["code"] for event in result["events"]} == {"R11"}


def test_missing_data_yields_unknown_not_false_event() -> None:
    result = evaluate_rules({"published": {}, "derived": {}})
    assert {event["code"] for event in result["events"]} == {"R08"}  # Sharpe null là trigger thật
    assert "R02" in result["unknown"]
    assert result["risk_level"] == "low"
