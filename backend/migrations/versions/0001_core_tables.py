"""Tạo bảng lõi Phase 1.

Revision ID: 0001_core_tables
Revises:
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_core_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role in ('admin','viewer')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "traders",
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("nickname", sa.String(length=255), nullable=True),
        sa.Column("nickname_translate", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("portfolio_type", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_trade_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("futures_type", sa.String(length=32), nullable=True),
        sa.Column("init_invest_asset", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("lead_portfolio_id"),
    )
    op.create_index("ix_traders_portfolio_type", "traders", ["portfolio_type"], unique=False)
    op.create_index("ix_traders_status", "traders", ["status"], unique=False)

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_hour", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
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
        sa.UniqueConstraint(
            "lead_portfolio_id",
            "collected_hour",
            "source",
            name="uq_portfolio_snapshot_hour_source",
        ),
    )
    op.create_index(
        "ix_snapshots_lookup",
        "portfolio_snapshots",
        ["lead_portfolio_id", "collected_hour"],
        unique=False,
    )

    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_portfolio_id", sa.String(length=64), nullable=False),
        sa.Column("time_range", sa.String(length=8), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("roi", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("pnl", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("mdd", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("copier_pnl", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("win_rate", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("win_orders", sa.Integer(), nullable=True),
        sa.Column("total_orders", sa.Integer(), nullable=True),
        sa.Column("sharpe", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["lead_portfolio_id"],
            ["traders.lead_portfolio_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lead_portfolio_id",
            "time_range",
            "collected_at",
            name="uq_performance_range_collected",
        ),
    )
    op.create_index(
        "ix_perf_lookup",
        "performance_metrics",
        ["lead_portfolio_id", "time_range", "collected_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_perf_lookup", table_name="performance_metrics")
    op.drop_table("performance_metrics")
    op.drop_index("ix_snapshots_lookup", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
    op.drop_index("ix_traders_status", table_name="traders")
    op.drop_index("ix_traders_portfolio_type", table_name="traders")
    op.drop_table("traders")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
