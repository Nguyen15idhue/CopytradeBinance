from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScoringConfig(Base):
    __tablename__ = "scoring_config_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    weights: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalization: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    hard_filters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
