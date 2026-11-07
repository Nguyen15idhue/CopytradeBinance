"""Bảng knowledge_chunks + full-text search (simple) cho code/docs.

Revision ID: 0017_knowledge_chunks
Revises: 0016_agent_views
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_knowledge_chunks"
down_revision: str | None = "0016_agent_views"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRIGGER_FN = """
CREATE OR REPLACE FUNCTION knowledge_chunks_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.tsv := to_tsvector('simple', coalesce(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql
"""

TRIGGER = """
CREATE TRIGGER trg_knowledge_chunks_tsv
BEFORE INSERT OR UPDATE OF content ON knowledge_chunks
FOR EACH ROW EXECUTE FUNCTION knowledge_chunks_tsv_update()
"""


def upgrade() -> None:
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("heading", sa.String(512), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "knowledge_chunks",
        sa.Column("tsv", postgresql.TSVECTOR(), nullable=True),
    )
    op.create_index("ix_knowledge_chunks_path", "knowledge_chunks", ["path"])
    op.create_index("ix_knowledge_chunks_source", "knowledge_chunks", ["source_type"])
    op.execute(TRIGGER_FN)
    op.execute(TRIGGER)
    op.execute("CREATE INDEX ix_knowledge_chunks_tsv ON knowledge_chunks USING gin(tsv)")
    op.execute("UPDATE knowledge_chunks SET content = content WHERE tsv IS NULL")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_knowledge_chunks_tsv ON knowledge_chunks")
    op.execute("DROP FUNCTION IF EXISTS knowledge_chunks_tsv_update()")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_tsv")
    op.drop_table("knowledge_chunks")
