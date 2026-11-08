from app.services.agent.verifier import (
    build_answer_contract,
    check_units,
    verify_answer,
    verify_copy_plan,
)
from app.services.copy_plan.planner import build_copy_plan


def test_hallucinated_number_flagged() -> None:
    facts = [{"id": "roi_90d", "value": 19.19, "unit": "%"}]
    result = verify_answer("ROI lên tới 250% thật ấn tượng.", facts, row_ids=[])
    assert result["unverified_numbers"]
    assert any("chưa có nguồn" in w for w in result["warnings"])


def test_grounded_numbers_pass() -> None:
    facts = [
        {"id": "roi_90d", "value": 19.19, "unit": "%"},
        {"id": "mdd_90d", "value": 8.54, "unit": "%"},
    ]
    result = verify_answer("ROI 19.19%, MDD 8.54%.", facts, row_ids=[])
    assert result["unverified_numbers"] == []
    assert result["unknown_ids"] == []


def test_mixed_trader_ids_flagged() -> None:
    result = verify_answer(
        "So sánh 5143921081414022657 và 5296057151807357697.",
        [],
        row_ids=["5143921081414022657"],
    )
    assert result["unknown_ids"] == ["5296057151807357697"]


def test_unit_mismatch_warning() -> None:
    facts = [{"id": "roi_90d", "value": 19.19, "unit": "%"}]
    warnings = check_units("ROI 19.19 USDT rất cao.", facts)
    assert warnings
    assert not check_units("ROI 19.19% rất cao.", facts)


def test_datetime_not_flagged_as_unverified() -> None:
    facts = [{"id": "roi_90d", "value": 38.49, "unit": "%"}]
    result = verify_answer(
        "Top 10 (snapshot lúc 2026-11-07 15:06 UTC): ROI 38.49%.",
        facts,
        row_ids=[],
    )
    assert result["unverified_numbers"] == []


def test_advice_gets_disclaimer() -> None:
    result = verify_answer("Bạn nên copy trader này ngay.", [], row_ids=[])
    assert "không phải lời khuyên đầu tư" in result["answer"]


def test_contract_confidence_levels() -> None:
    high = build_answer_contract("ok", [{"id": "a"}], [{"ref": "a"}])
    assert high["confidence"] == "high"
    medium = build_answer_contract("ok", [{"id": "a"}], [], warnings=["w"])
    assert medium["confidence"] == "medium"
    low = build_answer_contract("không rõ", [], [])
    assert low["confidence"] == "low"
    assert low["missing_data"] == []


def _plan() -> dict:
    return build_copy_plan(
        {"trader_id": "1234567890", "capital_usd": 100, "preferred_mode": "fixed_ratio"},
        {
            "fixed_radio_min_copy_usd": 100,
            "fixed_amount_min_copy_usd": 10,
            "profit_sharing_rate": 10,
        },
        {"mdd_90d": 20, "worst_position_roi": -35, "max_leverage": 20},
        margin_mode={"mode": "isolated", "confidence": 0.8},
    )


def test_verify_copy_plan_requires_known_evidence() -> None:
    plan = _plan()
    warnings = verify_copy_plan(plan, [])
    assert "copy_plan_evidence_unknown:1234567890:fixed_ratio_min_copy_usd" in warnings

    fact_ids = [
        {"id": "1234567890:fixed_ratio_min_copy_usd"},
        {"id": "1234567890:mdd_90d"},
        {"id": "1234567890:worst_position_roi"},
        {"id": "1234567890:max_leverage"},
        {"id": "1234567890:margin_mode"},
    ]
    assert verify_copy_plan(plan, fact_ids) == []


def test_verify_copy_plan_flags_bounds() -> None:
    plan = _plan()
    plan["total_stop_loss_usd"]["value"] = 9999
    warnings = verify_copy_plan(plan, [])
    assert "total_stop_loss_over_capital" in warnings
