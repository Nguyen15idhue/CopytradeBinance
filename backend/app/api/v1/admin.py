from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.api.response import ok
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
async def admin_ping(user: User = Depends(require_admin)) -> dict:
    return ok({"admin": True, "email": user.email})
