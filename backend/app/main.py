from collections import deque
from time import monotonic
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as api_v1_router
from app.core import metrics
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.rate_limit import limiter
from app.core.security import decode_token
from app.models.collection_log import CollectionLog

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_HITS: dict[str, deque[float]] = {}


def _rate_key(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        try:
            payload = decode_token(header[7:], expected_type="access")
            return f"user:{payload.get('sub')}"
        except Exception:  # noqa: BLE001 - token hỏng thì rate theo IP
            pass
    return f"ip:{request.client.host if request.client else 'unknown'}"


@app.middleware("http")
async def request_context(request: Request, call_next):
    started = monotonic()
    request.state.request_id = request.headers.get("X-Request-ID", uuid4().hex)
    path = request.url.path
    limit = get_settings().api_rate_limit_per_min
    if path.startswith(settings.api_v1_prefix) and request.method != "OPTIONS":
        key = _rate_key(request)
        window_start = monotonic() - 60
        hits = API_HITS.setdefault(key, deque())
        while hits and hits[0] < window_start:
            hits.popleft()
        if len(hits) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "data": None,
                    "meta": {"request_id": request.state.request_id},
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Vượt giới hạn 100 request/phút",
                        "details": {},
                    },
                },
                headers={"X-Request-ID": request.state.request_id},
            )
        hits.append(monotonic())
    response = await call_next(request)
    route = request.scope.get("route")
    metrics.observe(
        request.method,
        getattr(route, "path", path),
        response.status_code,
        monotonic() - started,
    )
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _error_body(
    code: str, message: str, details: dict | None = None, request_id: str | None = None
) -> dict:
    return {
        "data": None,
        "meta": {"request_id": request_id},
        "error": {"code": code, "message": message, "details": details or {}},
    }


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message, exc.details),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=_error_body("RATE_LIMITED", "Quá nhiều yêu cầu, vui lòng thử lại sau"),
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_body("VALIDATION_ERROR", "Dữ liệu không hợp lệ", {"errors": exc.errors()}),
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body("HTTP_ERROR", str(exc.detail)),
    )


app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@app.get("/metrics")
async def prometheus_metrics(db: AsyncSession = Depends(get_db)) -> Response:
    last = await db.scalar(
        select(func.max(CollectionLog.finished_at)).where(
            CollectionLog.layer == "L0", CollectionLog.status == "success"
        )
    )
    timestamp = last.timestamp() if last is not None else 0
    body = metrics.render() + f"collector_last_scan_success_timestamp {timestamp:.0f}\n"
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
