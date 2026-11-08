from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawArchiveManifest(Base):
    __tablename__ = "raw_archive_manifests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    layer: Mapped[str] = mapped_column(String(8), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    path_latest: Mapped[str | None] = mapped_column(Text)
    path_previous: Mapped[str | None] = mapped_column(Text)
    files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    records: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    checksum: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_raw_manifest_layer_status", "layer", "status"),
        Index("ix_raw_manifest_created", "created_at"),
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "scan_id": str(self.scan_id),
            "layer": self.layer,
            "endpoint": self.endpoint,
            "mode": self.mode,
            "status": self.status,
            "files": self.files,
            "bytes": self.bytes,
            "records": self.records,
        }
