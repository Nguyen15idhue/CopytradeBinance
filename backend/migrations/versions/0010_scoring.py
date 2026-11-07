"""Tạo bảng scoring_config_versions, trader_scores, ranking_snapshots.

Revision ID: 0010_scoring
Revises: 0009_risk_events
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_scoring"
down_revision: str | None = "0009_risk_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scoring_config_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalization", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hard_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", name="uq_scoring_config_version"),
    )
    op.create_index(
        "ix_scoring_config_active", "scoring_config_versions", ["is_active"], unique=False
    )

    op.create_table(
        "trader_scores",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("band", sa.String(length=16), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("rankable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "hard_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"], ["traders.lead_portfolio_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_portfolio_id", "config_version", name="uq_scores_lead_config"),
    )
    op.create_index("ix_scores_config_score", "trader_scores", ["config_version", "score"])

    op.create_table(
        "ranking_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("board", sa.String(length=24), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ranking_board_time", "ranking_snapshots", ["board", "collected_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ranking_board_time", table_name="ranking_snapshots")
    op.drop_table("ranking_snapshots")
    op.drop_index("ix_scores_config_score", table_name="trader_scores")
    op.drop_table("trader_scores")
    op.drop_index("ix_scoring_config_active", table_name="scoring_config_versions")
    op.drop_table("scoring_config_versions")
