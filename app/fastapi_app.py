# app/fastapi_app.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Sequence

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    OperationalError,
    StatementError,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.api.v1.routers.auth.router import router as auth_router
from app.api.v1.routers.helpdesk.tracker import router as helpdesk_tracker_router
from app.config import BASE_DIR, settings
from app.core.validation_i18n import localize_validation_errors
from app.database import engine, redis_client
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.requests_middleware import RequestIDMiddleware, TimingMiddleware
from app.web.routers.main import router as web_router

logger = logging.getLogger("oss")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, hsts: bool = True):
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-XSS-Protection", "0")
        if self.hsts and settings.ENABLE_HSTS:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response


def setup_cors(app: FastAPI, allow_origins: Sequence[str]) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allow_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Request-ID"],
        expose_headers=["Authorization", "X-Request-ID"],
        max_age=600,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Helpdesk API starting up...")

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Main database connected successfully")
    except Exception as e:
        logger.error(f"Main database connection failed: {e}", exc_info=True)

    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(
            "Redis unavailable: %s — app will work without cache/brute-force protection",
            e,
        )

    yield

    logger.info("Helpdesk API shutting down...")
    try:
        await engine.dispose()
        logger.info("DB engine disposed")
    except Exception as e:
        logger.error(f"Error disposing DB engine: {e}")

    try:
        await redis_client.aclose()
        logger.info("Redis client closed")
    except Exception as e:
        logger.error(f"Error closing Redis client: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Helpdesk API",
        description="Внутренний helpdesk",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
        lifespan=lifespan,
    )

    setup_cors(app, settings.CORS_ORIGINS)

    app.add_middleware(SecurityHeadersMiddleware, hsts=True)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(TimingMiddleware, logger=logger)
    app.add_middleware(RequestIDMiddleware)

    static_dir = BASE_DIR / "app" / "static"
    media_dir = Path(settings.MEDIA_DIR)
    static_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    templates_dir = Path(settings.TEMPLATES_DIR)
    templates_dir.mkdir(parents=True, exist_ok=True)
    app.state.templates = Jinja2Templates(directory=str(templates_dir))
    app.state.templates.env.globals["url_for"] = app.url_path_for

    def _format_duration(sec) -> str:
        if sec is None or sec < 0:
            return "—"
        sec = float(sec)
        d = int(sec // 86400)
        h = int((sec % 86400) // 3600)
        m = int((sec % 3600) // 60)
        if d:
            return f"{d} д. {h}:{m:02d}"
        if h:
            return f"{h}:{m:02d}"
        return f"{m} мин."

    app.state.templates.env.globals["format_duration"] = _format_duration

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        detail = localize_validation_errors(exc.errors())
        msgs = [str(d.get("msg") or "").strip() for d in detail if d.get("msg")]
        message = "; ".join(m for m in msgs if m) or None
        body: dict = {"detail": detail}
        if message:
            body["message"] = message
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTPException {exc.status_code}: {exc.detail}", extra={"path": request.url.path})
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error("SQLAlchemy error", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Database error"})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("Integrity error", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=400, content={"detail": "Validation or uniqueness error"})

    @app.exception_handler(OperationalError)
    async def db_connection_error_handler(request: Request, exc: OperationalError):
        logger.error("DB OperationalError", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        logger.warning("DB DataError", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=400, content={"detail": "Invalid data format"})

    @app.exception_handler(StatementError)
    async def statement_error_handler(request: Request, exc: StatementError):
        logger.error("SQL StatementError", exc_info=True, extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Query execution failed"})

    @app.get("/health", tags=["Health"], response_class=PlainTextResponse)
    async def health() -> str:
        return "ok"

    @app.get("/ready", tags=["Health"], response_class=PlainTextResponse)
    async def ready() -> str:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            raise HTTPException(status_code=503, detail="Service Unavailable") from e
        try:
            await redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis degraded: {e}")
        return "ready"

    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    app.include_router(helpdesk_tracker_router, prefix="/api")
    app.include_router(web_router, tags=["Web"])

    logger.info("Helpdesk app created")
    return app
