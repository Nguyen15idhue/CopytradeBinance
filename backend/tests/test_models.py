from app.models import Base


def test_core_tables_registered() -> None:
    assert {
        "users",
        "traders",
        "portfolio_snapshots",
        "performance_metrics",
        "sessions",
        "trader_universe",
    } <= set(Base.metadata.tables)


def test_performance_unique_constraint() -> None:
    table = Base.metadata.tables["performance_metrics"]
    names = {constraint.name for constraint in table.constraints}
    assert "uq_performance_range_collected" in names


def test_snapshot_unique_constraint() -> None:
    table = Base.metadata.tables["portfolio_snapshots"]
    names = {constraint.name for constraint in table.constraints}
    assert "uq_portfolio_snapshot_hour_source" in names


def test_trader_metric_multi_window_columns() -> None:
    table = Base.metadata.tables["trader_metrics"]
    expected = {
        f"{prefix}_{window}"
        for window in ("7d", "30d", "90d", "180d")
        for prefix in ("roi", "mdd", "sharpe", "copier_pnl", "win_rate_order")
    }
    missing = expected - set(table.columns.keys())
    assert not missing, f"Thiếu cột đa khung: {sorted(missing)}"
