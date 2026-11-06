from app.models import Base


def test_core_tables_registered() -> None:
    assert {
        "users",
        "traders",
        "portfolio_snapshots",
        "performance_metrics",
        "sessions",
    } <= set(Base.metadata.tables)


def test_performance_unique_constraint() -> None:
    table = Base.metadata.tables["performance_metrics"]
    names = {constraint.name for constraint in table.constraints}
    assert "uq_performance_range_collected" in names


def test_snapshot_unique_constraint() -> None:
    table = Base.metadata.tables["portfolio_snapshots"]
    names = {constraint.name for constraint in table.constraints}
    assert "uq_portfolio_snapshot_hour_source" in names
