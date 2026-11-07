from app.services.quant.builder import WINDOW_COLUMN_MAP, WINDOW_UPSERT_COLUMNS


def test_window_column_map_covers_three_windows() -> None:
    assert set(WINDOW_COLUMN_MAP) == {"7D", "30D", "180D"}
    expected = {
        f"{prefix}_{window}"
        for window in ("7d", "30d", "180d")
        for prefix in ("roi", "mdd", "sharpe", "copier_pnl", "win_rate_order")
    }
    assert set(WINDOW_UPSERT_COLUMNS) == expected
    assert len(WINDOW_UPSERT_COLUMNS) == 15


def test_window_mapping_keeps_null() -> None:
    published = {
        "7D": {"roi": None, "mdd": None, "sharpe": None,
               "copier_pnl": None, "win_rate_order": None},
        "30D": {"roi": 4.1, "mdd": 5.9, "sharpe": 0.67,
                "copier_pnl": -383.5, "win_rate_order": 45.45},
        "180D": {"roi": 12.5, "mdd": 8.1, "sharpe": 1.2,
                 "copier_pnl": 900.0, "win_rate_order": 52.0},
    }
    values: dict[str, object] = {}
    for window, mapping in WINDOW_COLUMN_MAP.items():
        data = published.get(window) or {}
        for source_key, column_name in mapping.items():
            values[column_name] = data.get(source_key)
    # Khung thiếu dữ liệu giữ None, không đổi thành 0.
    assert values["roi_7d"] is None
    assert values["copier_pnl_7d"] is None
    assert values["roi_30d"] == 4.1
    assert values["win_rate_order_180d"] == 52.0
    assert all(value != 0 for value in values.values() if value is None)
