"""Tạo bảng ai_reports và ai_usage.

Revision ID: 0012_ai_reports
Revises: 0011_saved_views
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_ai_reports"
down_revision: str | None = "0011_saved_views"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("model_role", sa.String(length=16), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=16), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "cost_usd", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0"
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_reports_trader_time", "ai_reports", ["lead_portfolio_id", "created_at"]
    )

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "cost_usd", sa.Numeric(precision=10, scale=6), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_day", "ai_usage", ["day"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_day", table_name="ai_usage")
    op.drop_table("ai_usage")
    op.drop_index("ix_ai_reports_trader_time", table_name="ai_reports")
    op.drop_table("ai_reports")
