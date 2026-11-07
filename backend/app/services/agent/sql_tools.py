"""Tool sql_query: SELECT/WITH read-only, chặn DDL/DML, giới hạn dòng/timeout."""

import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.schema import EvidenceItem, ToolResult, utcnow_iso
from app.services.agent.tools import register_tool

FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|"
    r"analyze|call|do|execute|comment|listen|notify|prepare|deallocate|checkpoint|"
    r"cluster|discard|handler|import|load|security|into|outfile|dumpfile)\b"
    r"|pg_catalog|information_schema"
    r"|\b(users|sessions|app_settings|alembic_version)\b",
    re.IGNORECASE,
)
LIMIT_RE = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)
MAX_ROWS = 500
DEFAULT_ROWS = 200


def validate_sql(raw: str) -> tuple[str, str | None]:
    """Trả (query chuẩn hóa, lỗi)."""
    query = re.sub(r"/\*.*?\*/", " ", raw or "", flags=re.DOTALL)
    query = re.sub(r"--[^\n]*", " ", query).strip()
    if not query:
        return "", "Query rỗng"
    body = query[:-1].strip() if query.endswith(";") else query
    if ";" in body:
        return "", "Chỉ cho phép 1 statement"
    first = body.split(None, 1)[0].lower() if body.split(None, 1) else ""
    if first not in ("select", "with"):
        return "", "Chỉ cho phép SELECT/WITH"
    if FORBIDDEN_RE.search(body):
        return "", "Query chứa từ khóa/bảng bị cấm"
    match = LIMIT_RE.search(body)
    if match and int(match.group(1)) > MAX_ROWS:
        return "", f"Limit tối đa {MAX_ROWS}"
    if not match:
        body = f"{body} LIMIT {DEFAULT_ROWS}"
    return body, None


@register_tool(
    "sql_query",
    "Truy vấn read-only toàn bộ dữ liệu nghiệp vụ (SELECT/WITH, tối đa 500 dòng).",
    {"type": "object", "properties": {"query": {"type": "string"}},
     "required": ["query"]},
)
async def sql_query(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    query, error = validate_sql(str(args.get("query") or ""))
    if error:
        return ToolResult.fail(error)
    started = time.perf_counter()
    engine = db.bind
    try:
        assert engine is not None
        async with engine.connect() as conn:
            trans = await conn.begin()
            try:
                await conn.execute(text("SET TRANSACTION READ ONLY"))
                await conn.execute(text("SET LOCAL statement_timeout = '5s'"))
                cursor = await conn.execute(text(query))
                rows = [dict(row) for row in cursor.mappings().all()]
                await trans.rollback()
            except BaseException:
                await trans.rollback()
                raise
    except Exception as exc:  # noqa: BLE001
        return ToolResult.fail(f"SQL lỗi: {str(exc)[:300]}")
    duration = round((time.perf_counter() - started) * 1000)
    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    return ToolResult(
        data={"rows": rows, "row_count": len(rows), "truncated": truncated,
              "duration_ms": duration},
        meta={"source": "database", "as_of": utcnow_iso(), "row_ids": []},
        evidence=[EvidenceItem(id="sql_row_count", label="Số dòng",
                               value=len(rows), unit="rows",
                               source="database", as_of=utcnow_iso())],
    )
