from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.api.service_deps import get_auth_service
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.config import get_settings
from app.core.errors import AppError
from app.infrastructure.db.session import get_db
from app.infrastructure.db.models import User
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.service.auth_cookies import clear_auth_cookies, set_auth_cookies
from app.modules.identity.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_REGISTER_LIMITS = (
    RateLimitRule(key_template="auth:register:ip:{ip}", limit=5, window_seconds=15 * 60),
)

_LOGIN_LIMITS = (
    RateLimitRule(key_template="auth:login:ip:{ip}", limit=10, window_seconds=5 * 60),
    RateLimitRule(key_template="auth:login:email:{email}", limit=8, window_seconds=10 * 60),
)

_REFRESH_LIMITS = (
    RateLimitRule(key_template="auth:refresh:ip:{ip}", limit=30, window_seconds=5 * 60),
)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    ip = await enforce_request_rate_limits(request, _REGISTER_LIMITS)
    tokens = await svc.register(
        body,
        client_ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    # Ensure newly created user/session rows are committed before issuing tokens.
    await session.commit()
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=tokens.access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    ip = await enforce_request_rate_limits(
        request,
        _LOGIN_LIMITS,
        values={"email": body.email.lower()},
    )
    tokens = await svc.login(
        body,
        client_ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    # Commit refresh-token rotation/state before returning an access token to clients.
    await session.commit()
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ip = await enforce_request_rate_limits(request, _REFRESH_LIMITS)
    refresh_token = request.cookies.get(get_settings().refresh_token_cookie_name)
    if not refresh_token:
        raise AppError(
            code="refresh_token_missing",
            message="Your session has ended. Please log in again.",
            status_code=401,
        )
    try:
        session_tokens = await svc.refresh_session(
            refresh_token=refresh_token,
            client_ip=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except AppError:
        # Persist security revocations triggered during refresh failures (reuse/expiry).
        await session.commit()
        raise
    set_auth_cookies(
        response,
        access_token=session_tokens.access_token,
        refresh_token=session_tokens.refresh_token,
        settings=get_settings(),
    )
    return TokenResponse(access_token=session_tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    viewer: User | None = Depends(get_optional_user),
    svc: AuthService = Depends(get_auth_service),
) -> Response:
    refresh_token = request.cookies.get(get_settings().refresh_token_cookie_name)
    await svc.logout(
        refresh_token=refresh_token,
        user_id=viewer.id if viewer else None,
    )
    clear_auth_cookies(response, settings=get_settings())
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
