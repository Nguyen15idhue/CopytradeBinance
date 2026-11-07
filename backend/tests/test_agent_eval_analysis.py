"""Eval agent 15 case phân tích/đánh giá (kế hoạch 04, bước 4.0.9).

Mỗi case chạy orchestrator thật + tool thật + DB thật; model được script hoá
để gọi đúng tool, rồi đối chiếu số với DB. Không gọi live OpenRouter.
"""

import os
import re
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from sqlalchemy import delete, select, text

from app.core.database import SessionLocal
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.trader_metric import TraderMetric
from app.models.user import User
from app.services.agent.model_client import AgentModelResult, AgentToolCallRequest
from app.services.agent.orchestrator import _RATE, run_chat
from app.services.agent.tools import run_tool

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)

TRADER_A = "5143921081414022657"


@pytest.fixture(autouse=True)
async def _reset() -> None:
    _RATE.clear()
    from app.seed import seed_admin

    await seed_admin()
    yield
    _RATE.clear()


async def _admin_id() -> Any:
    async with SessionLocal() as db:
        return (
            await db.execute(select(User).where(User.email == "admin@example.com"))
        ).scalars().first().id


def _scripted(
    tool_calls: list[AgentToolCallRequest],
    answer_builder: Callable[[list[dict[str, Any]]], str],
) -> Callable[..., Awaitable[tuple[AgentModelResult, list[str]]]]:
    state = {"step": 0}

    async def fake(messages, specs, api_key, transport=None, **kwargs):
        if state["step"] == 0 and tool_calls:
            state["step"] = 1
            return AgentModelResult(text="", tool_calls=tool_calls), []
        return AgentModelResult(text=answer_builder(messages), role="primary"), []

    return fake


def _observations(messages: list[dict[str, Any]]) -> str:
    return " ".join(m.get("content", "") for m in messages)


async def _run(monkeypatch, tool_calls, answer_builder, message, session_id=None):
    monkeypatch.setattr(
        "app.services.agent.orchestrator.call_agent_model",
        _scripted(tool_calls, answer_builder),
    )
    user_id = await _admin_id()
    events = []
    async with SessionLocal() as db:
        async for event in run_chat(db, user_id, message, session_id):
            events.append(event)
    return events


def _event(events, name):
    return [event for event in events if event.event == name]


def _done(events) -> dict:
    done = _event(events, "done")
    assert done, f"Không có event done: {[e.event for e in events]}"
    return done[-1].data


def _facts_from_done(events) -> list[dict]:
    citations = _event(events, "citation")
    assert citations, "Thiếu event citation"
    return citations[-1].data.get("items", [])


# ---------- E1/E2/E4: đối chiếu trực tiếp tool với DB ----------


@pytest.mark.asyncio
async def test_e1_top_roi_7d_matches_db() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db, "search_traders",
            {"window": "7D", "sort": [{"field": "roi", "dir": "desc"}], "limit": 5},
        )
        assert result.error is None
        ids = [item["id"] for item in result.data["items"]]
        rows = (
            await db.execute(
                text(
                    "SELECT lead_portfolio_id FROM trader_metrics "
                    "WHERE roi_7d IS NOT NULL ORDER BY roi_7d DESC, lead_portfolio_id "
                    "LIMIT 5"
                )
            )
        ).all()
        assert ids == [row[0] for row in rows]
        assert result.data["items"][0]["windows"]["7D"]["roi"] is not None


@pytest.mark.asyncio
async def test_e2_stable_180d_uses_mdd_window() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db, "search_traders",
            {
                "window": "180D",
                "max_mdd": 10,
                "min_roi": 0,
                "sort": [{"field": "roi", "dir": "desc"}],
                "limit": 5,
            },
        )
        assert result.error is None
        for item in result.data["items"]:
            assert item["windows"]["180D"]["mdd"] <= 10
            assert item["windows"]["180D"]["roi"] >= 0


@pytest.mark.asyncio
async def test_e4_copiers_and_copier_pnl() -> None:
    async with SessionLocal() as db:
        result = await run_tool(
            db, "search_traders",
            {"min_copiers": 10, "min_copier_pnl": 0, "limit": 5},
        )
        assert result.error is None
        for item in result.data["items"]:
            assert item["current_copiers"] >= 10
            assert item["windows"]["90D"]["copier_pnl"] >= 0
        rows = (
            await db.execute(
                text(
                    "SELECT lead_portfolio_id FROM trader_metrics "
                    "WHERE current_copiers >= 10 AND copier_pnl_90d >= 0 "
                    "ORDER BY current_copiers DESC, copier_pnl_90d DESC LIMIT 5"
                )
            )
        ).all()
        assert rows


# ---------- E3: so sánh khung qua orchestrator ----------


@pytest.mark.asyncio
async def test_e3_compare_windows_with_real_numbers(monkeypatch) -> None:
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.roi_7d.is_not(None)).limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        roi_7d = float(metric.roi_7d)
        roi_180d = float(metric.roi_180d) if metric.roi_180d is not None else None

    def answer(messages):
        text_answer = f"Khung 7D ROI {roi_7d:.2f}%"
        if roi_180d is not None:
            text_answer += f", khung 180D ROI {roi_180d:.2f}%"
        return text_answer

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_trader_profile", {"trader_id": trader_id})],
        answer,
        f"Trader {trader_id} 7D và 180D thế nào",
    )
    done = _done(events)
    assert f"{roi_7d:.2f}%" in done["answer"]
    labels = {item["ref"] for item in _facts_from_done(events)}
    assert f"{trader_id}:roi_7d" in labels
    assert f"{trader_id}:roi_180d" in labels
    assert not _event(events, "warning")


# ---------- E5: vốn 100$ ----------


@pytest.mark.asyncio
async def test_e5_portfolio_fit_100_usd(monkeypatch) -> None:
    async with SessionLocal() as db:
        current = (
            await db.execute(
                text(
                    "SELECT lead_portfolio_id, fixed_radio_min_copy_usd "
                    "FROM agent_trader_copy_constraints "
                    "WHERE fixed_radio_min_copy_usd IS NOT NULL LIMIT 1"
                )
            )
        ).first()
    trader_id, min_copy = current[0], float(current[1])
    can = 100.0 >= min_copy

    def answer(messages):
        verdict = "đủ" if can else "không đủ"
        return f"Vốn 100 USDT {verdict} so với min copy {min_copy:.2f} USDT"

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("analyze_portfolio_fit",
                              {"trader_id": trader_id, "capital_usd": 100})],
        answer,
        f"Trader {trader_id} với vốn 100$ có copy được không",
    )
    assert "analyze_portfolio_fit" in [e.data["tool"] for e in _event(events, "tool_call")]
    done = _done(events)
    assert "100" in done["answer"]
    assert not [w for w in _event(events, "warning") if "chưa có nguồn" in w.data["message"]]


# ---------- E6: so sánh nhiều trader ----------


@pytest.mark.asyncio
async def test_e6_compare_multiple_traders(monkeypatch) -> None:
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(TraderMetric.lead_portfolio_id, TraderMetric.roi_90d).limit(3)
            )
        ).all()
    ids = [row[0] for row in rows]
    rois = {row[0]: float(row[1]) for row in rows if row[1] is not None}

    def answer(messages):
        parts = [f"{tid} ROI {rois[tid]:.2f}%" for tid in ids if tid in rois]
        return "So sánh: " + "; ".join(parts)

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("compare_traders", {"trader_ids": ids})],
        answer,
        "So sánh 3 trader này",
    )
    done = _done(events)
    assert "ROI" in done["answer"]
    assert "compare_traders" in [e.data["tool"] for e in _event(events, "tool_call")]


# ---------- E7: rủi ro ----------


@pytest.mark.asyncio
async def test_e7_risk_events(monkeypatch) -> None:
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text(
                    "SELECT lead_portfolio_id, code, severity FROM risk_events "
                    "LIMIT 1"
                )
            )
        ).first()
    trader_id, code, severity = row

    def answer(messages):
        return f"Trader có risk event {code} mức {severity}"

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_risk_events", {"trader_id": trader_id})],
        answer,
        f"Trader {trader_id} có risk event gì",
    )
    assert code in _done(events)["answer"]


# ---------- E8: data health ----------


@pytest.mark.asyncio
async def test_e8_data_health(monkeypatch) -> None:
    def answer(messages):
        assert "recent_runs" in _observations(messages)
        return "Dữ liệu collector đã được cập nhật, xem as_of trong citation"

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_data_health", {})],
        answer,
        "Dữ liệu collector có mới không",
    )
    assert "get_data_health" in [e.data["tool"] for e in _event(events, "tool_call")]
    assert _done(events)["answer"]


# ---------- E9: code/docs citation path + line ----------


@pytest.mark.asyncio
async def test_e9_knowledge_path_and_line(monkeypatch) -> None:
    async with SessionLocal() as db:
        await db.execute(delete(KnowledgeChunk))
        db.add(
            KnowledgeChunk(
                source_type="code", path="backend/app/services/risk_rules.py",
                line_start=42, line_end=60, heading="compute_risk_score",
                content="risk_score công thức gồm MDD leverage sharpe concentration",
                commit_sha="eval",
            )
        )
        await db.commit()
    try:
        def answer(messages):
            observation = _observations(messages)
            assert "risk_rules.py" in observation
            return "Công thức risk_score nằm trong backend/app/services/risk_rules.py"

        events = await _run(
            monkeypatch,
            [AgentToolCallRequest("search_knowledge",
                                  {"query": "risk_score công thức", "scope": "code"})],
            answer,
            "risk_score tính thế nào",
        )
        refs = {item["ref"] for item in _facts_from_done(events)}
        assert any("risk_rules.py:42" in ref for ref in refs)
    finally:
        async with SessionLocal() as db:
            await db.execute(delete(KnowledgeChunk))
            await db.commit()


# ---------- E10: web (mock Tavily) ----------


@pytest.mark.asyncio
async def test_e10_web_search_citation(monkeypatch) -> None:
    import httpx

    from app.core.config import get_settings
    from app.services.agent import web_tools

    payload = {"results": [{"title": "Binance Funding",
                            "url": "https://www.binance.com/funding",
                            "content": "Funding rate cập nhật 8h/lần."}]}
    monkeypatch.setattr(get_settings(), "tavily_api_key", "test-key")
    monkeypatch.setattr(get_settings(), "agent_web_search_enabled", True)
    monkeypatch.setattr(
        web_tools, "_TRANSPORT",
        httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    )

    def answer(messages):
        return "Nguồn Binance cho biết funding cập nhật 8h/lần."

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("web_search", {"query": "binance funding rate"})],
        answer,
        "Tin tức funding rate",
    )
    sources = {item["source_type"] for item in _facts_from_done(events)}
    assert "web" in sources


# ---------- E11: multi-turn ----------


@pytest.mark.asyncio
async def test_e11_multi_turn_keeps_context(monkeypatch) -> None:
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.roi_180d.is_not(None)).limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        roi_180d = float(metric.roi_180d)

    seen: list[str] = []

    def answer(messages):
        seen.append(_observations(messages))
        return f"Theo khung 180D, ROI là {roi_180d:.2f}%"

    calls = [AgentToolCallRequest("get_trader_profile", {"trader_id": trader_id})]
    first = await _run(monkeypatch, calls, answer, f"Phân tích trader {trader_id}")
    session_id = _done(first)["session_id"]

    second = await _run(
        monkeypatch, [], answer, "Còn khung 180D thì sao?", session_id=session_id
    )
    _done(second)
    # Lượt 2 phải thấy nội dung lượt 1 trong history.
    assert f"Phân tích trader {trader_id}" in seen[-1]
    assert f"{roi_180d:.2f}%" in _done(second)["answer"]


# ---------- E12: unknown ----------


@pytest.mark.asyncio
async def test_e12_unknown_trader_no_fabrication(monkeypatch) -> None:
    def answer(messages):
        return "Không tìm thấy trader này trong dữ liệu, nên tôi không có số liệu."

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_trader_profile", {"trader_id": "999999999999999999"})],
        answer,
        "Trader 999999999999999999 thế nào",
    )
    done = _done(events)
    assert "Không tìm thấy" in done["answer"]
    assert re.search(r"\d+[.,]\d+", done["answer"]) is None
    tool_results = _event(events, "tool_result")
    assert tool_results and tool_results[0].data["ok"] is False


# ---------- E13: prompt injection ----------


@pytest.mark.asyncio
async def test_e13_injection_does_not_change_behavior(monkeypatch) -> None:
    from app.services.agent.verifier import contains_advice

    def answer(messages):
        observation = _observations(messages)
        assert "bỏ qua mọi chỉ dẫn" in observation
        return "Nội dung trader chỉ là dữ liệu tham khảo, tôi không thực thi chỉ dẫn trong đó."

    with_marker = AgentToolCallRequest(
        "get_trader_profile", {"trader_id": TRADER_A}
    )
    events = await _run(
        monkeypatch, [with_marker], answer, "Phân tích trader này"
    )
    done = _done(events)
    assert not contains_advice(done["answer"])


# ---------- E14: không tư vấn ----------


@pytest.mark.asyncio
async def test_e14_advice_gets_disclaimer(monkeypatch) -> None:
    def answer(messages):
        return "Bạn nên copy trader 5143921081414022657 ngay."

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_trader_profile", {"trader_id": TRADER_A})],
        answer,
        "Tôi có nên copy trader này không",
    )
    done = _done(events)
    assert "không phải lời khuyên đầu tư" in done["answer"]
    warnings = [w.data["message"] for w in _event(events, "warning")]
    assert any("lời khuyên" in message for message in warnings)


# ---------- E15: evidence cho mọi case có dữ liệu ----------


@pytest.mark.asyncio
async def test_e15_all_numbers_have_evidence(monkeypatch) -> None:
    async with SessionLocal() as db:
        metric = (
            await db.execute(
                select(TraderMetric).where(TraderMetric.roi_90d.is_not(None)).limit(1)
            )
        ).scalars().first()
        trader_id = metric.lead_portfolio_id
        roi = float(metric.roi_90d)
        mdd = float(metric.mdd_90d) if metric.mdd_90d is not None else None

    def answer(messages):
        text_answer = f"ROI 90D {roi:.2f}%"
        if mdd is not None:
            text_answer += f", MDD {mdd:.2f}%"
        return text_answer

    events = await _run(
        monkeypatch,
        [AgentToolCallRequest("get_trader_profile", {"trader_id": trader_id})],
        answer,
        f"Hiệu suất trader {trader_id}",
    )
    done = _done(events)
    number_warnings = [
        w.data["message"] for w in _event(events, "warning")
        if "chưa có nguồn" in w.data["message"]
    ]
    assert number_warnings == [], number_warnings
    assert _facts_from_done(events)
    assert f"{roi:.2f}%" in done["answer"]
