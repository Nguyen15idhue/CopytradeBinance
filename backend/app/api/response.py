from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request


def ok(data, request: Request | None = None) -> dict:
    request_id = getattr(request.state, "request_id", None) if request else None
    return {
        "data": data,
        "meta": {
            "request_id": request_id or uuid4().hex,
            "generated_at": datetime.now(UTC).isoformat(),
        },
        "error": None,
    }
