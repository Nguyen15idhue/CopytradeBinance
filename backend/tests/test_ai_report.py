import json

import httpx
import pytest

from app.core.config import get_settings
from app.services.ai.openrouter import AIError, generate_report, parse_json
from app.services.ai.prompt import template_report
from app.services.ai.schema import AIReportPayload

CONTEXT = {
    "id": "42",
    "tier": "qualified_upper",
    "confidence": 0.9,
    "published": {"roi": 20.0, "mdd": 10.0, "sharpe": 2.0, "total_orders": 100},
    "derived": {"max_leverage": 5.0, "worst_position_roi": -20.0, "profit_factor": 1.5},
    "flags": ["missing_benchmark"],
    "risk_events": [{"code": "R02", "label": "MDD > 20%"}],
    "allowed_evidence_ids": ["id", "roi_90d", "mdd_90d", "R02"],
}

GOOD = {
    "summary": "Trader có ROI dương và MDD trong ngưỡng, dữ liệu đủ để tham khảo.",
    "strengths": ["ROI 90D dương"],
    "weaknesses": ["Thiếu benchmark"],
    "risk_flags": ["R02: MDD > 20%"],
    "missing_data": ["benchmark"],
    "evidence_ids": ["id", "roi_90d", "R02"],
}


def _response(body: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": "fake-model",
            "choices": [{"message": {"content": json.dumps(body, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "cost": 0},
        },
    )


def test_parse_json_accepts_fenced() -> None:
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_rejects_garbage() -> None:
    with pytest.raises(AIError):
        parse_json("không phải json")


def test_schema_rejects_investment_advice() -> None:
    with pytest.raises(ValueError):
        AIReportPayload(
            summary="Bạn nên mua trader này ngay lập tức để có lợi nhuận.",
            strengths=["ROI cao"],
            weaknesses=["MDD"],
            risk_flags=[],
            missing_data=[],
            evidence_ids=["id"],
        )


def test_template_is_deterministic_and_uses_evidence() -> None:
    first = template_report(CONTEXT)
    second = template_report(CONTEXT)
    assert first.model_dump() == second.model_dump()
    assert "42" in first.summary
    assert "roi_90d" in first.evidence_ids
    assert first.risk_flags


@pytest.mark.asyncio
async def test_primary_success(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_model_primary", "primary-model")
    monkeypatch.setattr(settings, "ai_model_fallback", "fallback-model")
    transport = httpx.MockTransport(lambda request: _response(GOOD))
    result, errors = await generate_report(CONTEXT, "key", transport=transport)
    assert result.role == "primary"
    assert errors == []
    assert result.payload.evidence_ids == GOOD["evidence_ids"]


@pytest.mark.asyncio
async def test_primary_invalid_json_falls_back(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_model_primary", "primary-model")
    monkeypatch.setattr(settings, "ai_model_fallback", "fallback-model")
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "không phải json"}}], "usage": {}},
            )
        return _response(GOOD)

    result, errors = await generate_report(
        CONTEXT, "key", transport=httpx.MockTransport(handler)
    )
    assert result.role == "fallback"
    assert errors and "primary" in errors[0]


@pytest.mark.asyncio
async def test_both_fail_use_template(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_model_primary", "primary-model")
    monkeypatch.setattr(settings, "ai_model_fallback", "fallback-model")
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    result, errors = await generate_report(CONTEXT, "key", transport=transport)
    assert result.role == "template"
    assert len(errors) == 2
    assert result.payload.summary


@pytest.mark.asyncio
async def test_evidence_outside_allowlist_rejected(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_model_primary", "primary-model")
    monkeypatch.setattr(settings, "ai_model_fallback", "")
    bad = dict(GOOD, evidence_ids=["id", "secret_field"])
    transport = httpx.MockTransport(lambda request: _response(bad))
    result, errors = await generate_report(CONTEXT, "key", transport=transport)
    assert result.role == "template"
    assert errors
