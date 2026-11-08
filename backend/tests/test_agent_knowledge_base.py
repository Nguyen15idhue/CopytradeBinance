"""Câu hỏi kiến thức: phải trả lời được kể cả khi full-text index rỗng."""

import pytest

from app.services.agent.knowledge import search_index
from app.services.agent.knowledge_base import search_concepts

CASES = [
    ("các nhóm a b c và bị loại là gì", "Nhóm trader A / B / C / Bị loại", "05-pheu"),
    ("tier high qualified watch excluded khác gì", "Nhóm trader", "05-pheu"),
    ("sharpe là gì", "Sharpe", "06-bo-chi-so"),
    ("mdd tính thế nào", "MDD", "06-bo-chi-so"),
    ("winrate order và winrate vị thế", "WinRate", "06-bo-chi-so"),
    ("điểm rủi ro risk score", "Điểm rủi ro", "08-risk"),
    ("mức điểm band good average", "Mức điểm", "07-scoring"),
    ("ba bảng xếp hạng low risk", "Ba bảng xếp hạng", "09-ranking"),
    ("copier pnl là gì", "Copier PnL", "02-copy-trading"),
    ("các khung 7d 30d 90d 180d", "Bốn khung", "04-du-lieu"),
    ("pre_score và confidence", "pre_score", "04-du-lieu"),
    ("profit factor và phí rebate", "Profit factor", "06-bo-chi-so"),
    ("dữ liệu cũ freshness", "Độ mới dữ liệu", "11-data-health"),
    ("đòn bẩy leverage", "Đòn bẩy", "08-risk"),
]


def test_knowledge_base_covers_concepts() -> None:
    for query, expected_heading, expected_path in CASES:
        items = search_concepts(query)
        assert items, f"Không khớp concept cho: {query}"
        joined = " ".join(item["heading"] + item["snippet"] for item in items)
        assert expected_heading.lower() in joined.lower(), query
        assert any(expected_path in item["path"] for item in items), query


@pytest.mark.asyncio
async def test_search_index_falls_back_to_concepts_when_empty() -> None:
    from app.core.database import SessionLocal

    async with SessionLocal() as db:
        result = await search_index(db, "các nhóm a b c và bị loại là gì", scope="all")
        assert result.error is None
        assert result.data["items"], "Không có kết quả cho câu hỏi khái niệm"
        concept_items = [item for item in result.data["items"] if item.get("anchor")]
        assert concept_items, "Không có concept KB trong kết quả"
        top = concept_items[0]
        assert "nhóm" in (top["heading"] + top["snippet"]).lower()
        assert "high_upper" in top["snippet"] or "Cao (A" in top["snippet"]
        assert result.evidence


@pytest.mark.asyncio
async def test_search_index_concept_answers_key_question() -> None:
    from app.core.database import SessionLocal

    async with SessionLocal() as db:
        result = await search_index(db, "nhóm A B C bị loại", scope="docs")
        assert result.error is None
        snippets = " ".join(
            item["snippet"] for item in result.data["items"] if item.get("anchor")
        )
        for token in ("Cao (A", "Đạt (B", "Theo dõi (C", "Bị loại"):
            assert token in snippets, token
