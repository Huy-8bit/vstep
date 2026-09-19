import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import (
    auth,
    learning,
    library,
    progress,
    pronunciation,
    reading,
    speaking,
    vocabulary,
    writing,
)
from app.common.errors import AppError
from app.core.config import settings
from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    yield
    await engine.dispose()


app = FastAPI(title="VSTEP Practice Platform", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def request_guards(request: Request, call_next):
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        origin = request.headers.get("origin")
        # CLI clients without browser cookies can use the API. Browser writes require a trusted origin.
        if origin and origin.rstrip("/") != settings.frontend_url.rstrip("/"):
            return JSONResponse(
                {"detail": "Nguồn yêu cầu không được phép.", "code": "invalid_origin"},
                status_code=403,
            )
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Yêu cầu không hợp lệ."}, status_code=403)
        audio_upload = request.url.path.startswith(
            ("/api/v1/speaking/answers/", "/api/v1/speaking/pronunciation/practices/")
        ) and request.url.path.endswith("/audio")
        library_upload = request.url.path == "/api/v1/my-questions/assets"
        if (audio_upload or library_upload) and not request.headers.get("content-length"):
            return JSONResponse(
                {"detail": "Upload tệp cần Content-Length.", "code": "length_required"}, status_code=411
            )
        limit = (
            settings.max_speaking_audio_mb * 1024 * 1024 + 65536
            if audio_upload
            else (
                21 * 1024 * 1024
                if request.url.path == "/api/v1/my-questions/assets"
                else 2 * 1024 * 1024
                if request.url.path.startswith("/api/v1/my-questions")
                else 100000
            )
        )
        try:
            content_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Kích thước yêu cầu không hợp lệ."}, status_code=400)
        if content_length > limit:
            return JSONResponse({"detail": "Nội dung quá dài."}, status_code=413)
        path = request.url.path
        if path.endswith(
            (
                "/parse",
                "/assets",
                "/login",
                "/register",
                "/grade",
                "/generate",
                "/transcribe",
                "/analyze",
                "/tts",
                "/explain",
                "/regrade",
                "/calibrate",
                "/feedback",
                "/vocabulary",
                "/recommendations",
                "/answer",
                "/lesson",
                "/practice",
                "/targeted-practice",
                "/recalculate",
                "/summary",
            )
        ):
            now = time.monotonic()
            # Bounded, single-worker MVP rate limiter; do not trust forwarded IP headers.
            for key in list(hits):
                if not hits[key] or hits[key][-1] < now - 60:
                    del hits[key]
            key = f"{request.client.host if request.client else 'unknown'}:{path.split('/')[-1]}"
            bucket = hits[key]
            while bucket and bucket[0] < now - 60:
                bucket.popleft()
            if len(bucket) >= 20:
                return JSONResponse(
                    {
                        "detail": "Quá nhiều yêu cầu. Vui lòng thử lại sau một phút.",
                        "code": "rate_limited",
                    },
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            bucket.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(AppError)
async def app_error(request: Request, exc: AppError):
    return JSONResponse({"detail": exc.message, "code": exc.code}, status_code=exc.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        {
            "detail": "Đề chưa hợp lệ. Kiểm tra nội dung, số câu, lựa chọn và các trường đang nhập."
            if request.url.path.startswith("/api/v1/my-questions")
            else "Dữ liệu không hợp lệ. Kiểm tra email, mật khẩu (8–128 ký tự) và các lựa chọn.",
            "code": "validation_error",
            "fields": [".".join(str(x) for x in e["loc"]) for e in exc.errors()],
        },
        status_code=422,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.error("Unhandled application error: %s", type(exc).__name__)
    return JSONResponse(
        {
            "detail": "Đã xảy ra lỗi máy chủ. Vui lòng thử lại.",
            "code": "internal_error",
        },
        status_code=500,
    )


@app.get("/api/v1/health", tags=["Health"])
async def health():
    async with SessionLocal() as db:
        await db.execute(text("SELECT 1"))
    return {"status": "ok", "ai_configured": bool(settings.openai_api_key)}


for router in (
    auth.router,
    writing.router,
    progress.router,
    speaking.router,
    pronunciation.router,
    reading.router,
    vocabulary.router,
    library.router,
    learning.router,
):
    app.include_router(router, prefix="/api/v1")
