"""Gọi OpenRouter: primary → fallback, JSON schema validate."""

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.ai.prompt import SYSTEM_PROMPT, build_prompt
from app.services.ai.schema import AIReportPayload


class AIError(Exception):
    pass


@dataclass
class AIResult:
    payload: AIReportPayload
    role: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float = 0.0
    latency_ms: int | None = None


def parse_json(content: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise AIError("Không tìm thấy JSON trong phản hồi")
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AIError(f"JSON không hợp lệ: {exc}") from exc
    if not isinstance(data, dict):
        raise AIError("Phản hồi không phải object JSON")
    return data


async def call_model(
    model: str,
    prompt: str,
    api_key: str,
    base_url: str,
    timeout: int,
    max_tokens: int,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AIResult:
    if not model:
        raise AIError("Model id trống")
    if not api_key:
        raise AIError("Thiếu OPENROUTER_API_KEY")
    started = time.perf_counter()
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "reasoning": {"effort": "low"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:8090",
                    "X-Title": "CopytradeBinance",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise AIError(f"network: {exc}") from exc
    latency = round((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        raise AIError(f"HTTP {response.status_code}: {response.text[:200]}")
    body = response.json()
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    try:
        parsed = AIReportPayload.model_validate(parse_json(content))
    except Exception as exc:  # noqa: BLE001
        raise AIError(f"Schema không hợp lệ: {exc}") from exc
    usage = body.get("usage") or {}
    return AIResult(
        payload=parsed,
        role="primary",
        model=body.get("model") or model,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        cost_usd=float(usage.get("cost") or 0.0),
        latency_ms=latency,
    )


async def generate_report(
    context: dict[str, Any],
    api_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
    primary_model: str | None = None,
    fallback_model: str | None = None,
    max_tokens: int | None = None,
    timeout: int | None = None,
) -> tuple[AIResult, list[str]]:
    """Trả (result, lỗi từng lần thử). Fallback 1 lần, cuối cùng template."""
    settings = get_settings()
    prompt = build_prompt(context)
    errors: list[str] = []
    allowed = set(context.get("allowed_evidence_ids", []))
    for role, model in (
        ("primary", primary_model or settings.ai_model_primary),
        ("fallback", fallback_model or settings.ai_model_fallback),
    ):
        try:
            result = await call_model(
                model,
                prompt,
                api_key,
                settings.openrouter_base_url,
                timeout or settings.ai_timeout_seconds,
                max_tokens or settings.ai_max_tokens,
                transport=transport,
            )
            invalid = [item for item in result.payload.evidence_ids if item not in allowed]
            if invalid or not result.payload.evidence_ids:
                raise AIError(f"evidence_ids ngoài danh sách: {invalid[:3]}")
            result.role = role
            return result, errors
        except AIError as exc:
            errors.append(f"{role}/{model}: {exc}")
    from app.services.ai.prompt import template_report

    return (
        AIResult(
            payload=template_report(context),
            role="template",
            model="template",
            cost_usd=0.0,
            latency_ms=None,
        ),
        errors,
    )
