"""Model client cho agent: OpenRouter primary → fallback 1 lần.

Hỗ trợ native tool calling; model không hỗ trợ → JSON tool protocol.
Mặc định trong test dùng transport mock, không gọi live.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.ai.openrouter import AIError, build_reasoning

TOOL_PROTOCOL_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass
class AgentToolCallRequest:
    name: str
    arguments: dict[str, Any]


@dataclass
class AgentModelResult:
    text: str
    tool_calls: list[AgentToolCallRequest] = field(default_factory=list)
    role: str = "primary"
    model: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float = 0.0
    latency_ms: int | None = None


def parse_tool_protocol(text: str) -> list[AgentToolCallRequest]:
    """Fallback JSON tool protocol khi model không gọi tool native."""
    cleaned = (text or "").strip()
    candidates = [cleaned]
    match = TOOL_PROTOCOL_RE.search(cleaned)
    if match:
        candidates.append(match.group(1))
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(cleaned[start : end + 1])
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        calls = payload.get("tool_calls") if isinstance(payload, dict) else None
        if isinstance(calls, list):
            out = []
            for item in calls:
                if isinstance(item, dict) and item.get("name"):
                    args = item.get("arguments") or {}
                    out.append(AgentToolCallRequest(name=item["name"], arguments=args))
            if out:
                return out
    return []


def _openrouter_tools(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec.get("description", ""),
                "parameters": spec.get("parameters", {"type": "object"}),
            },
        }
        for spec in specs
    ]


async def _call_once(
    model: str,
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
    api_key: str,
    base_url: str,
    timeout: int,
    max_tokens: int,
    transport: httpx.AsyncBaseTransport | None,
) -> AgentModelResult:
    if not model:
        raise AIError("Model id trống")
    if not api_key:
        raise AIError("Thiếu OPENROUTER_API_KEY")
    started = time.perf_counter()
    body: dict[str, Any] = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "reasoning": build_reasoning(model),
        "messages": messages,
    }
    if tool_specs:
        body["tools"] = _openrouter_tools(tool_specs)
        body["tool_choice"] = "auto"
    try:
        async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:8090",
                    "X-Title": "CopytradeBinance-Agent",
                },
                json=body,
            )
    except httpx.HTTPError as exc:
        raise AIError(f"network: {exc}") from exc
    latency = round((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        raise AIError(f"HTTP {response.status_code}: {response.text[:200]}")
    payload = response.json()
    message = (payload.get("choices") or [{}])[0].get("message", {})
    text = message.get("content") or ""
    calls: list[AgentToolCallRequest] = []
    for item in message.get("tool_calls") or []:
        fn = (item or {}).get("function", {})
        if not fn.get("name"):
            continue
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        calls.append(AgentToolCallRequest(name=fn["name"], arguments=args))
    if not calls and tool_specs:
        calls = parse_tool_protocol(text)
        if calls:
            text = ""
    usage = payload.get("usage") or {}
    return AgentModelResult(
        text=text,
        tool_calls=calls,
        model=payload.get("model") or model,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        cost_usd=float(usage.get("cost") or 0.0),
        latency_ms=latency,
    )


async def call_agent_model(
    messages: list[dict[str, Any]],
    tool_specs: list[dict[str, Any]],
    api_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
    primary_model: str | None = None,
    fallback_model: str | None = None,
) -> tuple[AgentModelResult, list[str]]:
    """Gọi primary, lỗi thì fallback 1 lần. Trả (result, errors)."""
    settings = get_settings()
    key = api_key or settings.openrouter_api_key
    errors: list[str] = []
    for role, model in (
        ("primary", primary_model or settings.ai_model_primary),
        ("fallback", fallback_model or settings.ai_model_fallback),
    ):
        try:
            result = await _call_once(
                model,
                messages,
                tool_specs,
                key,
                settings.openrouter_base_url,
                settings.ai_timeout_seconds,
                settings.ai_max_tokens,
                transport,
            )
            result.role = role
            return result, errors
        except AIError as exc:
            errors.append(f"{role}/{model}: {exc}")
    raise AIError("; ".join(errors) if errors else "Không gọi được model")
