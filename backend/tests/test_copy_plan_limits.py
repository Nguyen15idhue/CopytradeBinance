from app.core.config import Settings
from app.services.copy_plan.limits import (
    COPY_LIMITS_VERSION,
    DEFAULT_LIMITS,
    CopyLimits,
    limits_from_settings,
)


def test_default_limits_match_binance_form() -> None:
    limits = CopyLimits()
    assert limits.ratio_copy_min_usd == 10
    assert limits.ratio_copy_max_usd == 300_000
    assert limits.amount_order_min_usd == 10
    assert limits.amount_order_max_usd == 50_000
    assert limits.amount_copy_min_usd == 10
    assert limits.amount_copy_max_usd == 300_000
    assert limits.tp_min_pct == 0
    assert limits.tp_max_pct == 2_000
    assert limits.sl_min_pct == 0
    assert limits.sl_max_pct == 95
    assert limits.max_cost_order_pct_min == 5
    assert limits.max_cost_order_pct_max == 95
    assert DEFAULT_LIMITS.version == COPY_LIMITS_VERSION


def test_limits_from_settings_overrides_bounds() -> None:
    settings = Settings(copy_ratio_max_usd=123.0, copy_sl_max_pct=90.0)
    limits = limits_from_settings(settings)
    assert limits.ratio_copy_max_usd == 123.0
    assert limits.sl_max_pct == 90.0
    assert limits.version == COPY_LIMITS_VERSION


def test_agent_message_has_copy_plan_columns() -> None:
    from app.models import Base

    cols = set(Base.metadata.tables["agent_messages"].columns.keys())
    assert "copy_plan" in cols
    assert "copy_plan_version" in cols


def test_copy_plan_version_is_stable() -> None:
    assert COPY_LIMITS_VERSION == "2026-11-binance-copy-form-v1"
