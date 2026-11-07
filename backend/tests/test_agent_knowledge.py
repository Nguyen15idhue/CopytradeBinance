import os

import pytest

from app.services.agent.knowledge import chunk_file, search_index

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Cần PostgreSQL trong compose",
)


def test_chunk_markdown_by_heading() -> None:
    chunks = chunk_file("docs/a.md", "# T\n\n## M1\nnội dung 1\n\n## M2\nnội dung 2\n")
    assert len(chunks) >= 2
    assert all(chunk.source_type == "docs" for chunk in chunks)


def test_chunk_python_by_function() -> None:
    code = "def risk_score(mdd):\n    return mdd * 2\n\ndef other():\n    return 1\n"
    chunks = chunk_file("backend/app/x.py", code)
    assert [chunk.heading for chunk in chunks] == ["risk_score", "other"]
    assert chunks[0].line_start == 1


@pytest.mark.asyncio
async def test_search_knowledge_path_line() -> None:
    from sqlalchemy import delete

    from app.core.database import SessionLocal
    from app.models.knowledge_chunk import KnowledgeChunk

    async with SessionLocal() as db:
        await db.execute(delete(KnowledgeChunk))
        db.add(
            KnowledgeChunk(
                source_type="code", path="backend/app/services/risk_rules.py",
                line_start=10, line_end=30, heading="compute_risk_score",
                content="Công thức risk_score bằng 30*MDD cộng 20*leverage",
                commit_sha="test",
            )
        )
        await db.commit()
        result = await search_index(db, "risk_score công thức", scope="code")
        assert result.error is None
        assert result.data["items"]
        first = result.data["items"][0]
        assert first["path"] == "backend/app/services/risk_rules.py"
        assert first["line_start"] == 10
        await db.execute(delete(KnowledgeChunk))
        await db.commit()
