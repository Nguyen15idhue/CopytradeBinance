"""Index code/docs + tool search_knowledge (full-text PostgreSQL)."""

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.agent.schema import EvidenceItem, ToolResult, utcnow_iso
from app.services.agent.tools import register_tool

EXCLUDED = (".env", "data/", "node_modules/", "dist/", "graphify-out/",
            ".git/", "__pycache__/", ".venv/")
CODE_EXTS = {".py", ".ts", ".tsx"}
MAX_FILE_BYTES = 200_000
MAX_CHUNK_CHARS = 2000


@dataclass
class Chunk:
    source_type: str
    path: str
    line_start: int | None
    line_end: int | None
    heading: str | None
    content: str


def _allowed(relative: str) -> bool:
    name = relative.replace("\\", "/")
    return not any(part in name for part in EXCLUDED)


def _chunk_markdown(relative: str, lines: list[str]) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading: str | None = None
    start = 1
    buf: list[str] = []

    def flush(end: int) -> None:
        text_content = "".join(buf).strip()
        if text_content:
            chunks.append(Chunk("docs", relative, start, end, heading,
                               text_content[:MAX_CHUNK_CHARS]))

    for i, line in enumerate(lines, start=1):
        if line.startswith("## ") and buf:
            flush(i - 1)
            buf = []
            start = i
        if line.startswith("#"):
            heading = line.strip("# ").strip()[:200]
        buf.append(line)
        if sum(len(part) for part in buf) > MAX_CHUNK_CHARS:
            flush(i)
            buf = []
            start = i + 1
    flush(len(lines))
    return chunks


def _chunk_python(relative: str, source: str) -> list[Chunk]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_window("code", relative, source.splitlines())
    lines = source.splitlines()
    chunks: list[Chunk] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", None) or node.lineno
            body = "\n".join(lines[node.lineno - 1 : end])[:MAX_CHUNK_CHARS]
            chunks.append(Chunk("code", relative, node.lineno, end, node.name, body))
    if not chunks:
        chunks = _chunk_window("code", relative, lines)
    return chunks


def _chunk_window(source_type: str, relative: str, lines: list[str]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for i in range(0, len(lines), 100):
        window = lines[i : i + 100]
        text_content = "\n".join(window).strip()
        if text_content:
            chunks.append(Chunk(source_type, relative, i + 1, i + len(window),
                               None, text_content[:MAX_CHUNK_CHARS]))
    return chunks


def chunk_file(relative: str, content: str) -> list[Chunk]:
    suffix = Path(relative).suffix.lower()
    if suffix == ".md":
        return _chunk_markdown(relative, content.splitlines(keepends=True))
    if suffix == ".py":
        return _chunk_python(relative, content)
    return _chunk_window("code", relative, content.splitlines())


def repo_root() -> Path:
    """Tìm gốc repo: thư mục chứa docs/ và app/ (host) hoặc /app (container)."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "docs").is_dir():
            return candidate
    return Path.cwd()


def collect_files(root: Path) -> list[Path]:
    roots = [
        root / "docs",
        root / "backend" / "app",
        root / "app",
        root / "frontend" / "src",
    ]
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in CODE_EXTS | {".md"}:
                continue
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            if _allowed(str(path.relative_to(root))):
                files.append(path)
    return files


def current_commit_sha(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root,
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


async def index_files(
    db: AsyncSession, root: Path, dry_run: bool = False,
) -> dict[str, Any]:
    sha = current_commit_sha(root)
    files = collect_files(root)
    chunks: list[Chunk] = []
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        chunks.extend(chunk_file(str(path.relative_to(root)), content))
    stats = {"files": len(files), "chunks": len(chunks), "commit_sha": sha,
             "dry_run": dry_run}
    if dry_run:
        return stats
    await db.execute(delete(KnowledgeChunk))
    for chunk in chunks:
        db.add(KnowledgeChunk(source_type=chunk.source_type, path=chunk.path,
                              line_start=chunk.line_start, line_end=chunk.line_end,
                              heading=chunk.heading, content=chunk.content,
                              commit_sha=sha))
    await db.commit()
    return stats


async def search_index(
    db: AsyncSession, query: str, scope: str = "all", limit: int = 10,
) -> ToolResult:
    cleaned = re.sub(r"\s+", " ", query or "").strip()
    if not cleaned:
        return ToolResult.fail("Thiếu query")
    scope = scope if scope in ("code", "docs") else "all"
    limit = max(1, min(int(limit or 10), 10))
    statement = (
        select(
            KnowledgeChunk,
            func.ts_headline(
                "simple", KnowledgeChunk.content,
                func.plainto_tsquery("simple", cleaned),
                "MaxWords=40, MinWords=15",
            ).label("headline"),
        )
        .where(KnowledgeChunk.tsv.op("@@")(func.plainto_tsquery("simple", cleaned)))
        .order_by(
            func.ts_rank(KnowledgeChunk.tsv,
                         func.plainto_tsquery("simple", cleaned)).desc()
        )
        .limit(limit)
    )
    if scope != "all":
        statement = statement.where(KnowledgeChunk.source_type == scope)
    rows = (await db.execute(statement)).all()
    items = [
        {"path": row.path, "line_start": row.line_start, "line_end": row.line_end,
         "heading": row.heading, "snippet": headline or row.content[:500]}
        for row, headline in rows
    ]
    if scope != "code":
        from app.services.agent.knowledge_base import search_concepts

        seen = {item.get("heading") for item in items}
        for concept in search_concepts(cleaned, 2):
            if concept["heading"] not in seen:
                items.append(concept)
            if len(items) >= limit:
                break
        items = items[:limit]
    used_kb = bool(items) and all(item.get("anchor") for item in items)
    if not items:
        from app.services.agent.knowledge_base import search_concepts

        items = search_concepts(cleaned, limit)
        if items:
            return ToolResult(
                data={"items": items, "total": len(items), "scope": scope,
                      "source": "concept_kb"},
                meta={"source": "docs", "as_of": utcnow_iso(), "row_ids": [],
                      "kb_fallback": True},
                evidence=[
                    EvidenceItem(
                        id=f"kb:{item['path']}:{index}",
                        label=item["heading"] or item["path"],
                        value=item["path"],
                        unit="path",
                        source="docs",
                        as_of=utcnow_iso(),
                    )
                    for index, item in enumerate(items)
                ],
            )
    return ToolResult(
        data={"items": items, "total": len(items), "scope": scope},
        meta={"source": "docs" if scope == "docs" else "code",
              "as_of": utcnow_iso(), "row_ids": [], "kb_fallback": used_kb},
        evidence=[
            EvidenceItem(id=f"kb:{item['path']}:{item['line_start']}",
                         label=item["heading"] or item["path"],
                         value=item["path"], unit="path",
                         source="docs" if scope == "docs" else "code",
                         as_of=utcnow_iso())
            for item in items
        ],
    )


@register_tool(
    "search_knowledge",
    "Tìm trong code/docs đã index (trả path + line + snippet).",
    {"type": "object",
     "properties": {"query": {"type": "string"},
                    "scope": {"type": "string"},
                    "limit": {"type": "integer"}},
     "required": ["query"]},
)
async def search_knowledge(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    return await search_index(
        db, str(args.get("query") or ""),
        str(args.get("scope") or "all"), args.get("limit") or 10,
    )


async def count_chunks(db: AsyncSession) -> int:
    return await db.scalar(select(func.count()).select_from(KnowledgeChunk)) or 0
