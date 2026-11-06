"""Tạo bảng trader_universe cho tier/reason.

Revision ID: 0003_trader_universe
Revises: 0002_sessions
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_trader_universe"
down_revision: str | None = "0002_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trader_universe",
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("potential_tier", sa.String(length=16), nullable=False),
        sa.Column("pre_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column(
            "filter_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "deep_fetch_status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"],
            ["traders.lead_portfolio_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("lead_portfolio_id"),
    )
    op.create_index(
        "ix_universe_tier", "trader_universe", ["potential_tier"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_universe_tier", table_name="trader_universe")
    op.drop_table("trader_universe")
