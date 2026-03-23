from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger

configure_logging(get_settings().debug)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("starting", app=get_settings().app_name)
    yield
    log.info("shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def cache_control(request: Request, call_next):
        response = await call_next(request)
        if request.method != "GET":
            return response
        path = request.url.path
        if path in ("/health", "/api/v1/billing/plans"):
            response.headers["Cache-Control"] = "public, max-age=120"
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )

    @app.get("/health")
    async def health_root() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"service": settings.app_name, "docs": "/docs"}

    app.include_router(api_router)
    return app


app = create_app()
