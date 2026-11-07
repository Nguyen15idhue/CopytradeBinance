from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy import Index as sa_Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (sa_Index("ix_agent_sessions_user_time", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Đoạn chat mới")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    __table_args__ = (
        sa_Index("ix_agent_messages_session_time", "session_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    facts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    assumptions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    missing_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"
    __table_args__ = (
        sa_Index("ix_agent_tool_calls_message", "message_id"),
        sa_Index("ix_agent_tool_calls_session_time", "session_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agent_messages.id", ondelete="SET NULL")
    )
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AgentCitation(Base):
    __tablename__ = "agent_citations"
    __table_args__ = (sa_Index("ix_agent_citations_message", "message_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_messages.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    ref: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    url: Mapped[str | None] = mapped_column(String(2048))
    snippet: Mapped[str | None] = mapped_column(Text)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentFeedback(Base):
    __tablename__ = "agent_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_messages.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
