from datetime import UTC, datetime, timedelta

import pytest

from app.services.quant.confidence import compute_confidence, label_for
from app.services.quant.metrics import (
    missing_flags,
    position_metrics,
    published_metrics,
    ratio_metrics,
    trade_metrics,
    transfer_metrics,
)


def _pos(pnl, roi, lev=10, side="Long", symbol="BTCUSDT", hours=10, notional=1000):
    opened = datetime(2026, 11, 1, tzinfo=UTC)
    return {
        "symbol": symbol,
        "side": side,
        "leverage": lev,
        "isolated": "Isolated",
        "opened_at": opened,
        "closed_at": opened + timedelta(hours=hours),
        "closing_pnl": pnl,
        "roi": roi,
        "max_open_interest": notional,
    }


def test_published_keeps_null_and_computes_order_win_rate() -> None:
    published = published_metrics(
        {
            "90D": {
                "roi": 12.5,
                "pnl": 100,
                "mdd": None,
                "sharpe": None,
                "win_orders": 5,
                "total_orders": 10,
            }
        }
    )
    assert published["90D"]["roi"] == 12.5
    assert published["90D"]["mdd"] is None
    assert published["90D"]["sharpe"] is None
    assert published["90D"]["win_rate_order"] == 50.0
    assert published["7D"]["roi"] is None


def test_position_metrics_profit_factor_payoff_and_concentration() -> None:
    positions = [
        _pos(100, 0.1, notional=800, symbol="BTCUSDT"),
        _pos(50, 0.05, notional=100, symbol="ETHUSDT"),
        _pos(-30, -0.03, notional=100, symbol="ETHUSDT"),
        _pos(-20, -0.9, notional=50, symbol="SOLUSDT"),
        _pos(10, 0.01, notional=50, side="Short"),
        _pos(-5, -0.01, notional=50, side="Short"),
    ]
    result = position_metrics(positions)
    assert result["positions_count"] == 6
    assert result["max_leverage"] == 10
    assert result["profit_factor"] == pytest.approx(160 / 55, rel=1e-4)
    assert result["payoff_ratio"] == pytest.approx((160 / 3) / (55 / 3), rel=1e-4)
    assert result["worst_position_roi"] == pytest.approx(-90.0)
    # -90% thuộc R06 (≤ -80%), không còn bị đếm trùng ở R14.
    assert result["near_liquidation_count"] == 0
    assert result["top_symbol"] == "BTCUSDT"
    assert result["top_symbol_share"] == pytest.approx(900 / 1150 * 100, rel=1e-4)
    assert result["median_holding_hours"] == 10
    assert result["position_win_rate"] == pytest.approx(3 / 6 * 100)


def test_near_liquidation_band_does_not_duplicate_r06() -> None:
    # R14 chỉ đếm vị thế lỗ sâu trong khoảng (-80%, -50%]; -85% và -100% thuộc R06.
    positions = [
        _pos(-100, -1.0),
        _pos(-85, -0.85),
        _pos(-60, -0.6),
        _pos(-50, -0.5),
        _pos(-40, -0.4),
    ]
    result = position_metrics(positions)
    assert result["worst_position_roi"] == pytest.approx(-100.0)
    assert result["near_liquidation_count"] == 2


def test_position_metrics_empty_is_null_not_zero() -> None:
    result = position_metrics([])
    assert result["profit_factor"] is None
    assert result["position_win_rate"] is None
    assert result["max_leverage"] is None


def test_trade_metrics_rebate_is_negative_fee() -> None:
    trades = [
        {
            "quantity": 1000,
            "fee": -5,
            "realized_profit": 100,
            "trade_time": datetime(2026, 11, 1, tzinfo=UTC),
        },
        {
            "quantity": 500,
            "fee": -2,
            "realized_profit": -20,
            "trade_time": datetime(2026, 11, 1, tzinfo=UTC),
        },
        {
            "quantity": 300,
            "fee": -1,
            "realized_profit": 0,
            "trade_time": datetime(2026, 11, 2, tzinfo=UTC),
        },
    ]
    result = trade_metrics(trades)
    assert result["total_fills"] == 3
    assert result["total_fees"] == -8
    assert result["fee_drag_pct"] == pytest.approx(-8 / 80 * 100)
    assert result["active_days"] == 2
    assert result["fills_per_day"] == 1.5


def test_transfer_net_flow() -> None:
    result = transfer_metrics(
        [
            {"amount": 1000, "trans_type": "LEAD_DEPOSIT"},
            {"amount": 400, "trans_type": "LEAD_WITHDRAW"},
            {"amount": 100, "trans_type": "LEAD_INVEST"},
        ]
    )
    assert result["net_flow"] == 700


def test_calmar_null_when_mdd_zero() -> None:
    published = published_metrics({"90D": {"roi": 20, "mdd": 0}})
    derived = ratio_metrics(published, {"positions_count": 10}, 1000, 500, 10, 10)
    assert derived["calmar"] is None
    assert derived["copy_aum_ratio"] == 50


def test_missing_flags_do_not_invent_values() -> None:
    metrics = {
        "published": published_metrics({"90D": {"roi": 1, "mdd": None, "sharpe": None}}),
        "derived": {"low_sample": True, "insufficient_positions": True},
        "trades": {"total_fills": 0},
        "benchmark_return": None,
    }
    flags = missing_flags(metrics)
    assert {"missing_mdd", "missing_sharpe", "missing_benchmark", "low_sample"} <= set(flags)


def test_confidence_low_for_young_portfolio() -> None:
    result = compute_confidence(
        {"roi": 60, "pnl": 1, "mdd": 30, "sharpe": None, "win_rate": 50,
         "total_orders": 10, "aum": 1000, "copy_aum": 0, "current_copiers": 0,
         "runtime_days": 4, "max_leverage": 10, "position_win_rate": 50},
        runtime_days=4,
        freshness_minutes=10,
        days_with_snapshot=1,
    )
    assert result["value"] < 0.6
    assert result["label"] == "low"
    assert label_for(0.8) == "high"
    assert label_for(0.6) == "medium"
    assert label_for(0.4) == "low"
