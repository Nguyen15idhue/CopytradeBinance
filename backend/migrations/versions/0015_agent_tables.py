"""Tao bang agent sessions/messages/tool_calls/citations/feedback.

Revision ID: 0015_agent_tables
Revises: 0014_risk_v2
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_agent_tables"
down_revision: str | None = "0014_risk_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = sa.text("now()")
TS = sa.DateTime(timezone=True)


def _ts(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, TS, server_default=NOW, nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default="New chat"),
        sa.Column("model", sa.String(128), nullable=False, server_default=""),
        _ts("created_at"),
        _ts("updated_at"),
        sa.Column("archived_at", TS, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_sessions_user_time", "agent_sessions", ["user_id", "created_at"]
    )
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("facts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("citations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("assumptions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("missing_data", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        _ts("created_at"),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_messages_session_time", "agent_messages", ["session_id", "created_at"]
    )
    op.create_table(
        "agent_tool_calls",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("arguments", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="ok"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        _ts("created_at"),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["agent_messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_tool_calls_message", "agent_tool_calls", ["message_id"])
    op.create_index(
        "ix_agent_tool_calls_session_time", "agent_tool_calls", ["session_id", "created_at"]
    )
    op.create_table(
        "agent_citations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("ref", sa.String(512), nullable=False, server_default=""),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("as_of", TS, nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["agent_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_citations_message", "agent_citations", ["message_id"])
    op.create_table(
        "agent_feedback",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        _ts("created_at"),
        sa.ForeignKeyConstraint(["message_id"], ["agent_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_agent_feedback_message"),
    )
    op.add_column(
        "ai_usage",
        sa.Column("feature", sa.String(16), nullable=False, server_default="report"),
    )


def downgrade() -> None:
    op.drop_column("ai_usage", "feature")
    op.drop_table("agent_feedback")
    op.drop_index("ix_agent_citations_message", table_name="agent_citations")
    op.drop_table("agent_citations")
    op.drop_index("ix_agent_tool_calls_session_time", table_name="agent_tool_calls")
    op.drop_index("ix_agent_tool_calls_message", table_name="agent_tool_calls")
    op.drop_table("agent_tool_calls")
    op.drop_index("ix_agent_messages_session_time", table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_index("ix_agent_sessions_user_time", table_name="agent_sessions")
    op.drop_table("agent_sessions")
