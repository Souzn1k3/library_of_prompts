from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.config import get_settings
from app.core.errors import AppError
from app.core.rate_limit import get_rate_limiter
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_cookies import clear_auth_cookies, set_auth_cookies
from app.modules.identity.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        UserRepository(session),
        RefreshTokenRepository(session),
        get_settings(),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


def _client_ip(request: Request) -> str:
    settings = get_settings()
    if settings.rate_limit_trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_rate_limit(*, key: str, limit: int, window_seconds: int) -> None:
    allowed = await get_rate_limiter().allow(key=key, limit=limit, window_seconds=window_seconds)
    if allowed:
        return
    raise AppError(
        code="rate_limited",
        message="Too many requests. Please try again later.",
        status_code=429,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    svc: AuthService = Depends(auth_service),
) -> TokenResponse:
    ip = _client_ip(request)
    await _check_rate_limit(
        key=f"auth:register:ip:{ip}",
        limit=5,
        window_seconds=15 * 60,
    )
    session = await svc.register(
        body,
        client_ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    set_auth_cookies(
        response,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=session.access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    svc: AuthService = Depends(auth_service),
) -> TokenResponse:
    ip = _client_ip(request)
    email_key = body.email.lower()
    await _check_rate_limit(
        key=f"auth:login:ip:{ip}",
        limit=10,
        window_seconds=5 * 60,
    )
    await _check_rate_limit(
        key=f"auth:login:email:{email_key}",
        limit=8,
        window_seconds=10 * 60,
    )
    session = await svc.login(
        body,
        client_ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    set_auth_cookies(
        response,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=session.access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    svc: AuthService = Depends(auth_service),
) -> TokenResponse:
    ip = _client_ip(request)
    await _check_rate_limit(
        key=f"auth:refresh:ip:{ip}",
        limit=30,
        window_seconds=5 * 60,
    )
    refresh_token = request.cookies.get(get_settings().refresh_token_cookie_name)
    if not refresh_token:
        raise AppError(
            code="refresh_token_missing",
            message="Your session has ended. Please log in again.",
            status_code=401,
        )
    session = await svc.refresh_session(
        refresh_token=refresh_token,
        client_ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    set_auth_cookies(
        response,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=session.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    viewer: User | None = Depends(get_optional_user),
    svc: AuthService = Depends(auth_service),
) -> Response:
    refresh_token = request.cookies.get(get_settings().refresh_token_cookie_name)
    await svc.logout(
        refresh_token=refresh_token,
        user_id=viewer.id if viewer else None,
    )
    clear_auth_cookies(response, settings=get_settings())
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
