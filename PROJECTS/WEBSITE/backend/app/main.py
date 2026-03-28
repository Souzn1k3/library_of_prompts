from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.cache import get_cache
from app.core.errors import AppError
from app.core.i18n import resolve_language_from_header, translate
from app.core.logging import configure_logging, get_logger
from app.core.runtime_guard import verify_runtime_database
from app.infrastructure.db.session import engine

configure_logging(get_settings().debug)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    log.info("starting", app=settings.app_name, app_env=settings.app_env)
    await verify_runtime_database(engine, settings)
    yield
    await get_cache().close()
    log.info("shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = "/docs" if settings.debug else None
    redoc_url = "/redoc" if settings.debug else None
    openapi_url = "/openapi.json" if settings.debug else None
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id)
        return response

    @app.middleware("http")
    async def cache_control(request: Request, call_next):
        response = await call_next(request)
        if request.method != "GET":
            return response
        vary = response.headers.get("Vary")
        vary_tokens = {token.strip() for token in (vary or "").split(",") if token.strip()}
        if "Accept-Language" not in vary_tokens:
            vary_tokens.add("Accept-Language")
            response.headers["Vary"] = ", ".join(sorted(vary_tokens))
        path = request.url.path
        if path in ("/health", "/api/v1/billing/plans"):
            response.headers["Cache-Control"] = "public, max-age=120"
        return response

    @app.middleware("http")
    async def slow_request_logger(request: Request, call_next):
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (perf_counter() - started) * 1000
            if elapsed_ms >= settings.slow_request_threshold_ms:
                log.warning(
                    "slow_request_failed",
                    method=request.method,
                    path=request.url.path,
                    query=str(request.url.query),
                    status_code=500,
                    elapsed_ms=round(elapsed_ms, 2),
                )
            raise

        elapsed_ms = (perf_counter() - started) * 1000
        if elapsed_ms >= settings.slow_request_threshold_ms:
            log.warning(
                "slow_request",
                method=request.method,
                path=request.url.path,
                query=str(request.url.query),
                status_code=response.status_code,
                elapsed_ms=round(elapsed_ms, 2),
            )
        if settings.debug:
            response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response

    def _request_id(request: Request) -> str:
        request_id = getattr(request.state, "request_id", None)
        if isinstance(request_id, str) and request_id:
            return request_id
        generated = uuid4().hex
        request.state.request_id = generated
        return generated

    def _http_status_message_key(status_code: int) -> str:
        status_map = {
            400: "errors.bad_request",
            401: "errors.invalid_or_expired_token",
            403: "errors.insufficient_permissions",
            404: "errors.route_not_found",
            405: "errors.method_not_allowed",
            410: "errors.deprecated_endpoint",
            429: "errors.rate_limited",
            503: "errors.service_unavailable",
        }
        return status_map.get(status_code, "errors.request_failed")

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        language = resolve_language_from_header(request.headers.get("accept-language"))
        message_key = exc.message_key or f"errors.{exc.code}"
        localized_message = translate(message_key, language, exc.message_params)
        request_id = _request_id(request)
        details = dict(exc.details) if exc.details else {}
        details.setdefault("request_id", request_id)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": localized_message or exc.message,
                "details": details,
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        language = resolve_language_from_header(request.headers.get("accept-language"))
        request_id = _request_id(request)
        errors = jsonable_encoder(
            exc.errors(),
            custom_encoder={
                ValueError: str,
                Exception: str,
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": translate("errors.validation_failed", language)
                or "Please check your input and try again.",
                "details": {"errors": errors, "request_id": request_id},
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        language = resolve_language_from_header(request.headers.get("accept-language"))
        request_id = _request_id(request)

        localized = translate(_http_status_message_key(exc.status_code), language)
        if localized:
            message = localized
        elif isinstance(exc.detail, str) and exc.detail.strip():
            message = exc.detail
        else:
            message = translate("errors.request_failed", language) or "We couldn't complete that action."

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "http_error",
                "message": message,
                "details": {
                    "status_code": exc.status_code,
                    "request_id": request_id,
                },
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        language = resolve_language_from_header(request.headers.get("accept-language"))
        request_id = _request_id(request)
        log.exception(
            "unhandled_exception",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            error_type=exc.__class__.__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": translate("errors.internal_server_error", language)
                or "Something went wrong. Please try again.",
                "details": {"request_id": request_id},
            },
            headers={"X-Request-ID": request_id},
        )

    @app.get("/health")
    async def health_root() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, Any]:
        payload: dict[str, Any] = {"service": settings.app_name}
        if settings.debug:
            payload["docs"] = "/docs"
        return payload

    app.include_router(api_router)
    return app


app = create_app()
