"""Them bang collector_jobs (ke hoach 05, buoc 5.0.6).

Revision ID: 0020_collector_jobs
Revises: 0019_raw_archive_manifest
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_collector_jobs"
down_revision: str | None = "0019_raw_archive_manifest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collector_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collector_jobs_requested", "collector_jobs", ["requested_at"],
        postgresql_ops={"requested_at": "DESC"},
    )
    op.create_index("ix_collector_jobs_status", "collector_jobs", ["status", "requested_at"])


def downgrade() -> None:
    op.drop_index("ix_collector_jobs_status", table_name="collector_jobs")
    op.drop_index("ix_collector_jobs_requested", table_name="collector_jobs")
    op.drop_table("collector_jobs")
