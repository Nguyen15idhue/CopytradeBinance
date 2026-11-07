"""Agent orchestrator: planner + tool loop (tối đa 8 bước) + verifier + lưu DB."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models.agent import AgentCitation, AgentMessage, AgentSession, AgentToolCall
from app.services.agent.model_client import call_agent_model
from app.services.agent.schema import AgentAnswer, SseEvent, utcnow_iso
from app.services.agent.tools import check_agent_budget, record_agent_usage, run_tool, tool_specs
from app.services.agent.verifier import build_answer_contract, check_units, verify_answer

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI của hệ thống CopytradeBinance. Trả lời tiếng Việt, "
    "chỉ dùng số liệu từ tool, ghi rõ nguồn. Không đưa lời khuyên đầu tư. "
    "Khi câu hỏi liên quan ngắn hạn hay dài hạn, nêu rõ khung 7D/30D/90D/180D và "
    "hiển thị đủ các khung liên quan. Khung thiếu dữ liệu thì ghi unknown, không bịa số."
)

_RATE: dict[str, list[float]] = {}


def check_rate_limit(user_key: str, per_min: int) -> None:
    now = time.monotonic()
    window = [t for t in _RATE.get(user_key, []) if now - t < 60]
    if len(window) >= per_min:
        raise ApiError(429, "AGENT_RATE_LIMITED", "Gửi quá nhanh, thử lại sau")
    window.append(now)
    _RATE[user_key] = window


def compact_observation(data: Any, limit: int) -> str:
    """JSON compact; vượt giới hạn thì cắt có cấu trúc (không cắt giữa chuỗi)."""
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str)
    if len(serialized) <= limit:
        return serialized
    rows: list[Any] = []
    if isinstance(data, dict):
        for key in ("items", "rows"):
            if isinstance(data.get(key), list):
                rows = data[key]
                break
    kept: list[Any] = []
    size = 0
    for row in rows:
        row_size = len(
            json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str)
        )
        if size + row_size > limit - 200:
            break
        kept.append(row)
        size += row_size
    payload: dict[str, Any] = {
        "truncated": True,
        "omitted_rows": max(0, len(rows) - len(kept)),
        "hint": "gọi lại tool với limit nhỏ hơn hoặc lọc thêm để lấy dữ liệu đầy đủ",
    }
    if kept:
        key = "items" if isinstance(data, dict) and isinstance(data.get("items"), list) else "rows"
        payload[key] = kept
        if isinstance(data, dict):
            for extra in ("total", "config_version", "window", "as_of"):
                if extra in data:
                    payload[extra] = data[extra]
    else:
        payload["preview"] = serialized[: max(0, limit - 200)]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def template_from_evidence(evidence: list[dict]) -> str:
    """Fallback tất định khi model lỗi nhưng đã có dữ liệu tool."""
    lines = []
    for item in evidence[:8]:
        unit = f" {item.get('unit')}" if item.get("unit") else ""
        lines.append(f"- {item.get('label')}: {item.get('value')}{unit}")
    body = "\n".join(lines) if lines else "Chưa có số liệu."
    return f"Dựa trên {len(evidence)} kết quả truy vấn (model gặp lỗi nên tóm tắt tự động):\n{body}"


async def get_or_create_session(
    db: AsyncSession, user_id: UUID, session_id: int | None, model: str,
    title_hint: str | None = None,
) -> AgentSession:
    if session_id is not None:
        session = await db.get(AgentSession, session_id)
        if session is None or str(session.user_id) != str(user_id):
            raise ApiError(404, "AGENT_SESSION_NOT_FOUND", "Không tìm thấy đoạn chat")
        return session
    title = (title_hint or "").strip()[:60] or "Đoạn chat mới"
    session = AgentSession(user_id=user_id, title=title, model=model)
    db.add(session)
    await db.flush()
    return session


async def load_history(db: AsyncSession, session_id: int, limit: int = 10) -> list[dict]:
    """Nạp lượt chat trước để model có ngữ cảnh multi-turn."""
    rows = (
        await db.execute(
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    turns = [
        {"role": row.role, "content": (row.content or "")[:2000]}
        for row in reversed(rows)
        if row.role in ("user", "assistant")
    ]
    return turns


async def _save_message(
    db: AsyncSession,
    session: AgentSession,
    role: str,
    content: str,
    answer: AgentAnswer | None = None,
    tokens: int | None = None,
    cost: float = 0.0,
    latency_ms: int | None = None,
) -> AgentMessage:
    msg = AgentMessage(
        session_id=session.id,
        role=role,
        content=content,
        facts=(answer.facts if answer else []),
        citations=(answer.citations if answer else []),
        assumptions=(answer.assumptions if answer else []),
        missing_data=(answer.missing_data if answer else []),
        tokens=tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
    )
    db.add(msg)
    await db.flush()
    return msg


async def run_chat(
    db: AsyncSession,
    user_id: UUID,
    message: str,
    session_id: int | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AsyncIterator[SseEvent]:
    """SSE skeleton: tool loop giả lập, lưu session/message/tool/citation."""
    settings = get_settings()
    if not settings.agent_enabled:
        yield SseEvent("error", {"code": "AGENT_DISABLED", "message": "Agent đang tắt"})
        return
    check_rate_limit(str(user_id), settings.agent_rate_limit_per_min)
    from app.services.settings_service import get_ai_api_key, get_ai_config

    config = await get_ai_config(db)
    model = config.get("model_primary") or settings.ai_model_primary
    await check_agent_budget(db, settings.ai_daily_budget_usd, settings.ai_monthly_budget_usd)
    session = await get_or_create_session(db, user_id, session_id, model, message)
    prior_turns = await load_history(db, session.id)
    await _save_message(db, session, "user", message)
    session.updated_at = datetime.now().astimezone()
    await db.commit()

    history: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *prior_turns,
        {"role": "user", "content": message},
    ]
    specs = tool_specs()
    evidence: list[dict[str, Any]] = []
    row_ids: list[str] = []
    facts: list[dict[str, Any]] = []
    started = time.perf_counter()
    max_steps = settings.agent_max_steps
    api_key = await get_ai_api_key(db)
    assistant_text = ""
    total_prompt = 0
    total_completion = 0
    total_cost = 0.0

    try:
        for _step in range(max_steps):
            elapsed = time.perf_counter() - started
            if elapsed > settings.agent_timeout_seconds:
                yield SseEvent("warning", {"message": "Hết thời gian 120s, dừng tool loop"})
                break
            try:
                result, errors = await call_agent_model(
                    history, specs, api_key, transport=transport,
                )
            except Exception as exc:  # noqa: BLE001 - primary+fallback đều lỗi
                if evidence:
                    assistant_text = template_from_evidence(evidence)
                    yield SseEvent(
                        "warning",
                        {"message": f"Model lỗi ({str(exc)[:120]}) — trả lời từ dữ liệu tool"},
                    )
                    break
                raise
            total_prompt += result.prompt_tokens or 0
            total_completion += result.completion_tokens or 0
            total_cost += result.cost_usd or 0
            if not result.tool_calls:
                assistant_text = result.text or ""
                break
            for call in result.tool_calls:
                yield SseEvent(
                    "tool_call", {"tool": call.name, "arguments": call.arguments}
                )
                tool_started = time.perf_counter()
                try:
                    tool_result = await asyncio.wait_for(
                        run_tool(db, call.name, call.arguments), timeout=10,
                    )
                except TimeoutError:
                    tool_result = None
                    tool_error = "Tool quá 10s"
                else:
                    tool_error = tool_result.error
                duration = round((time.perf_counter() - tool_started) * 1000)
                db.add(
                    AgentToolCall(
                        session_id=session.id,
                        message_id=None,
                        tool_name=call.name,
                        arguments=call.arguments,
                        result_summary=(
                            compact_observation(tool_result.data, 2000)
                            if tool_result
                            else None
                        ),
                        status="ok" if not tool_error else "error",
                        duration_ms=duration,
                        error=tool_error,
                    )
                )
                if tool_result is not None and tool_result.ok:
                    for item in tool_result.evidence:
                        evidence.append(item.to_dict())
                        facts.append({"id": item.id, "value": item.value, "unit": item.unit})
                        if item.row_id:
                            row_ids.append(item.row_id)
                    observation = compact_observation(
                        tool_result.data, settings.agent_observation_chars
                    )
                else:
                    observation = f"Lỗi tool {call.name}: {tool_error}"
                yield SseEvent(
                    "tool_result",
                    {"tool": call.name, "ok": tool_error is None, "summary": observation[:500]},
                )
                history.append(
                    {"role": "user", "content": f"[tool {call.name}] {observation}"}
                )
        else:
            assistant_text = assistant_text or "Hết 8 bước tool mà chưa có đáp án."
            yield SseEvent("warning", {"message": "Đạt tối đa 8 bước tool"})

        checked = verify_answer(assistant_text, facts, row_ids or None)
        all_warnings = list(checked["warnings"]) + check_units(checked["answer"], facts)
        for warning in all_warnings:
            yield SseEvent("warning", {"message": warning})
        missing = [] if facts else ["chưa có dữ liệu từ tool"]
        assumptions = (
            ["Số liệu từ snapshot DB, có độ trễ so với dữ liệu live"] if facts else []
        )
        citations = [
            {
                "source_type": item.get("source", "database"),
                "ref": item.get("id", ""),
                "as_of": item.get("as_of"),
            }
            for item in evidence
        ]
        contract = build_answer_contract(
            checked["answer"], facts, citations, assumptions, missing, all_warnings,
        )
        answer = AgentAnswer(
            answer=contract["answer"] or "Xin lỗi, tôi chưa có dữ liệu để trả lời.",
            facts=contract["facts"],
            citations=contract["citations"],
            assumptions=contract["assumptions"],
            missing_data=contract["missing_data"],
            confidence=contract["confidence"],
        )
        latency = round((time.perf_counter() - started) * 1000)
        msg = await _save_message(
            db, session, "assistant", answer.answer, answer,
            tokens=(total_prompt + total_completion) or None,
            cost=total_cost, latency_ms=latency,
        )
        await record_agent_usage(db, model, total_prompt, total_completion, total_cost)
        for item in evidence:
            db.add(
                AgentCitation(
                    message_id=msg.id,
                    source_type=item.get("source", "database"),
                    ref=item.get("id", ""),
                    snippet=f"{item.get('label')}: {item.get('value')}",
                    as_of=None,
                )
            )
        await db.commit()
        yield SseEvent("citation", {"items": answer.citations})
        yield SseEvent(
            "done",
            {
                "session_id": session.id,
                "message_id": msg.id,
                "answer": answer.answer,
                "model": model,
                "usage": {
                    "prompt_tokens": total_prompt,
                    "completion_tokens": total_completion,
                    "cost_usd": total_cost,
                },
            },
        )
    except ApiError as exc:
        yield SseEvent("error", {"code": exc.code, "message": exc.message})
    except Exception as exc:  # noqa: BLE001
        yield SseEvent("error", {"code": "AGENT_FAILED", "message": str(exc)[:300]})


async def list_sessions(db: AsyncSession, user_id: UUID) -> list[AgentSession]:
    rows = (
        await db.execute(
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(AgentSession.updated_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return list(rows)


def utcnow_iso_alias() -> str:
    return utcnow_iso()
