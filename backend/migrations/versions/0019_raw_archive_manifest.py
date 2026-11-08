"""Them bang manifest cho raw archive (ke hoach 05, buoc 5.0.1).

Revision ID: 0019_raw_archive_manifest
Revises: 0018_metric_windows
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_raw_archive_manifest"
down_revision: str | None = "0018_metric_windows"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_archive_manifests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("layer", sa.String(8), nullable=False),
        sa.Column("endpoint", sa.String(64), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("path_latest", sa.Text(), nullable=True),
        sa.Column("path_previous", sa.Text(), nullable=True),
        sa.Column("files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("records", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purged_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_raw_manifest_created", "raw_archive_manifests", ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "ix_raw_manifest_layer_status",
        "raw_archive_manifests",
        ["layer", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_raw_manifest_layer_status", table_name="raw_archive_manifests")
    op.drop_index("ix_raw_manifest_created", table_name="raw_archive_manifests")
    op.drop_table("raw_archive_manifests")
