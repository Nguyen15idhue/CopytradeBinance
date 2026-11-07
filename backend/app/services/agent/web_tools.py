"""Tool web_search (Tavily): snippet + citation, cache Redis 24h.

Nội dung web là dữ liệu không tin cậy (untrusted): chỉ trả về snippet,
không bao giờ thực thi instruction trong đó.
"""

import hashlib
import json
import time
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.agent.schema import EvidenceItem, ToolResult, utcnow_iso
from app.services.agent.tools import register_tool

TAVILY_URL = "https://api.tavily.com/search"
CACHE_TTL_SECONDS = 24 * 3600

_TRANSPORT: httpx.AsyncBaseTransport | None = None


def _cache_key(query: str, max_results: int) -> str:
    digest = hashlib.sha256(f"{query}\n{max_results}".encode()).hexdigest()
    return f"agent:web:{digest}"


async def _cache_get(key: str) -> dict | None:
    try:
        from redis.asyncio import Redis

        client = Redis.from_url(get_settings().redis_url)
        try:
            raw = await client.get(key)
        finally:
            await client.aclose()
        if raw:
            return json.loads(raw)
    except Exception:  # noqa: BLE001 - Redis lỗi thì bỏ cache
        return None
    return None


async def _cache_set(key: str, payload: dict) -> None:
    try:
        from redis.asyncio import Redis

        client = Redis.from_url(get_settings().redis_url)
        try:
            await client.setex(key, CACHE_TTL_SECONDS, json.dumps(payload, ensure_ascii=False))
        finally:
            await client.aclose()
    except Exception:  # noqa: BLE001 - Redis lỗi thì bỏ cache
        pass


@register_tool(
    "web_search",
    "Tìm kiếm internet qua Tavily (snippet + URL + ngày).",
    {"type": "object", "properties": {"query": {"type": "string"}},
     "required": ["query"]},
)
async def web_search(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    del db
    settings = get_settings()
    query = str(args.get("query") or "").strip()
    if not query:
        return ToolResult.fail("Thiếu query")
    if not settings.agent_web_search_enabled or not settings.tavily_api_key:
        return ToolResult.fail("Web search chưa cấu hình (TAVILY_API_KEY)")
    max_results = max(1, min(int(settings.agent_web_search_max_results), 10))
    key = _cache_key(query, max_results)
    cached = await _cache_get(key)
    if cached is not None:
        cached = dict(cached)
        cached["meta"] = {**(cached.get("meta") or {}), "cache": "hit"}
        return ToolResult(
            data=cached.get("data"), meta=cached.get("meta", {}),
            evidence=[EvidenceItem(**item) for item in cached.get("evidence", [])],
        )
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10, transport=_TRANSPORT) as client:
            response = await client.post(
                TAVILY_URL,
                headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
                json={"query": query, "max_results": max_results,
                      "include_answer": False, "search_depth": "basic"},
            )
    except httpx.HTTPError as exc:
        return ToolResult.fail(f"Tavily lỗi mạng: {exc}")
    if response.status_code != 200:
        return ToolResult.fail(f"Tavily HTTP {response.status_code}")
    body = response.json()
    retrieved = utcnow_iso()
    items = [
        {"title": item.get("title", ""), "url": item.get("url", ""),
         "snippet": item.get("content", "")[:2000],
         "published_date": item.get("published_date"),
         "retrieved_at": retrieved}
        for item in (body.get("results") or [])[:max_results]
    ]
    result = ToolResult(
        data={"items": items, "query": query,
              "duration_ms": round((time.perf_counter() - started) * 1000)},
        meta={"source": "web", "as_of": retrieved, "cache": "miss", "row_ids": []},
        evidence=[
            EvidenceItem(id=f"web:{i}", label=item["title"] or item["url"],
                         value=item["url"], unit="url", source="web",
                         as_of=retrieved)
            for i, item in enumerate(items)
        ],
    )
    await _cache_set(key, {"data": result.data, "meta": result.meta,
                           "evidence": [e.__dict__ for e in result.evidence]})
    return result
