from app.services.ranking import select_boards


def _row(pid, score, rankable=True, runtime=200, mdd=10.0, lev=3.0, conf=0.9,
         consistency=80.0, roi=20.0, sharpe=1.2):
    return {
        "id": pid,
        "score": score,
        "rankable": rankable,
        "runtime_days": runtime,
        "mdd_90d": mdd,
        "max_leverage": lev,
        "confidence": conf,
        "consistency_score": consistency,
        "roi_90d": roi,
        "sharpe": sharpe,
    }


def test_overall_excludes_not_rankable() -> None:
    rows = [_row("a", 80), _row("b", 95, rankable=False)]
    boards = select_boards(rows)
    assert [item["id"] for item in boards["overall"]] == ["a"]


def test_low_risk_filters_leverage_and_mdd() -> None:
    rows = [
        _row("ok", 70),
        _row("high_lev", 90, lev=12.0),
        _row("high_mdd", 85, mdd=25.0),
        _row("young", 88, runtime=60),
        _row("low_conf", 92, conf=0.6),
        _row("neg_sharpe", 95, sharpe=-0.4),
        _row("null_sharpe", 96, sharpe=None),
    ]
    boards = select_boards(rows)
    assert [item["id"] for item in boards["low_risk"]] == ["ok"]


def test_consistency_uses_consistency_score_not_roi() -> None:
    rows = [
        _row("roi_king", 90, roi=200, consistency=40),
        _row("steady", 70, roi=15, consistency=95),
    ]
    boards = select_boards(rows)
    assert boards["consistency"][0]["id"] == "steady"


def test_overall_not_only_roi() -> None:
    rows = [_row("risky", 45, roi=500), _row("balanced", 78, roi=20)]
    boards = select_boards(rows)
    assert boards["overall"][0]["id"] == "balanced"


def test_top_n_limit() -> None:
    rows = [_row(f"t{index}", 50 + index) for index in range(60)]
    boards = select_boards(rows, top_n=50)
    assert len(boards["overall"]) == 50
