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


def test_raw_archive_manifest_table() -> None:
    table = Base.metadata.tables["raw_archive_manifests"]
    required = {
        "scan_id", "layer", "endpoint", "mode", "status", "path_latest",
        "path_previous", "files", "bytes", "records", "checksum", "error",
        "created_at", "rotated_at", "purged_at",
    }
    assert required <= set(table.columns.keys())
    index_names = {index.name for index in table.indexes}
    assert "ix_raw_manifest_layer_status" in index_names
    assert "ix_raw_manifest_created" in index_names
