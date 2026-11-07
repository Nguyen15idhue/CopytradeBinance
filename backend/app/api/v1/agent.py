"""Agent chat admin-only + SSE skeleton."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.api.response import ok
from app.core.database import get_db
from app.core.errors import ApiError
from app.models.agent import AgentFeedback, AgentMessage, AgentSession
from app.models.user import User
from app.services.agent.orchestrator import list_sessions, run_chat

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatBody(BaseModel):
    session_id: int | None = None
    message: str = Field(min_length=1, max_length=4000)


class PatchSessionBody(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    archived: bool | None = None


class FeedbackBody(BaseModel):
    message_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


def _serialize_session(session: AgentSession) -> dict:
    return {
        "id": session.id,
        "title": session.title,
        "model": session.model,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "archived_at": session.archived_at.isoformat() if session.archived_at else None,
    }


@router.post("/chat")
async def chat(
    body: ChatBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> StreamingResponse:
    async def stream():
        async for event in run_chat(db, user.id, body.message, body.session_id):
            yield event.encode()

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/sessions")
async def sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    rows = await list_sessions(db, user.id)
    return ok({"items": [_serialize_session(row) for row in rows]}, request)


@router.get("/sessions/{session_id}")
async def session_detail(
    session_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    from sqlalchemy import select

    session = await db.get(AgentSession, session_id)
    if session is None or str(session.user_id) != str(user.id):
        raise ApiError(404, "AGENT_SESSION_NOT_FOUND", "Không tìm thấy đoạn chat")
    rows = (
        await db.execute(
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at.asc())
            .limit(200)
        )
    ).scalars().all()
    return ok(
        {
            "session": _serialize_session(session),
            "messages": [
                {"id": m.id, "role": m.role, "content": m.content} for m in rows
            ],
        },
        request,
    )


@router.patch("/sessions/{session_id}")
async def patch_session(
    session_id: int,
    body: PatchSessionBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    from datetime import datetime

    session = await db.get(AgentSession, session_id)
    if session is None or str(session.user_id) != str(user.id):
        raise ApiError(404, "AGENT_SESSION_NOT_FOUND", "Không tìm thấy đoạn chat")
    if body.title is not None:
        session.title = body.title
    if body.archived is not None:
        session.archived_at = datetime.now().astimezone() if body.archived else None
    await db.commit()
    return ok(_serialize_session(session), request)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    session = await db.get(AgentSession, session_id)
    if session is None or str(session.user_id) != str(user.id):
        raise ApiError(404, "AGENT_SESSION_NOT_FOUND", "Không tìm thấy đoạn chat")
    await db.delete(session)
    await db.commit()
    return ok({"deleted": session_id}, request)


@router.post("/feedback")
async def feedback(
    body: FeedbackBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    msg = await db.get(AgentMessage, body.message_id)
    if msg is None:
        raise ApiError(404, "AGENT_MESSAGE_NOT_FOUND", "Không tìm thấy message")
    db.add(
        AgentFeedback(message_id=body.message_id, rating=body.rating, comment=body.comment)
    )
    await db.commit()
    return ok({"message_id": body.message_id, "rating": body.rating}, request)


@router.get("/health")
async def health(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    from app.core.config import get_settings

    settings = get_settings()
    return ok(
        {"enabled": settings.agent_enabled, "max_steps": settings.agent_max_steps},
        request,
    )
