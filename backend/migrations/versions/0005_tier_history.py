"""Tạo bảng tier_history.

Revision ID: 0005_tier_history
Revises: 0004_collection_logs
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_tier_history"
down_revision: str | None = "0004_collection_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tier_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("old_tier", sa.String(length=16), nullable=True),
        sa.Column("new_tier", sa.String(length=16), nullable=False),
        sa.Column("pre_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"],
            ["traders.lead_portfolio_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tier_history_lead_changed",
        "tier_history",
        ["lead_portfolio_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_tier_history_lead_changed", table_name="tier_history")
    op.drop_table("tier_history")
