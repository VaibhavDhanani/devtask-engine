import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.db.database import async_session, dispose_engine
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.modules.auth.routes import router as auth_router
from app.modules.content.routes import router as content_router
from app.modules.user.routes import router as user_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("startup", app=settings.app_name, env=settings.environment)
    try:
        yield
    finally:
        await dispose_engine()
        log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url="/redoc" if not settings.is_prod else None,
        openapi_url="/openapi.json" if not settings.is_prod else None,
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled_exception")
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        log.info("request", status=response.status_code, duration_ms=round(duration_ms, 2))
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(user_router, prefix="/users", tags=["users"])
    app.include_router(content_router, prefix="/content", tags=["content"])

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/db", tags=["meta"])
    async def health_db() -> JSONResponse:
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:
            log.warning("db_health_failed", error=str(exc))
            return JSONResponse(
                status_code=503,
                content={"status": "error", "database": "unreachable"},
            )
        return JSONResponse(content={"status": "ok", "database": "reachable"})

    return app


app = create_app()
