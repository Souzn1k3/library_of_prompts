from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.api.service_deps import get_auth_service
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.config import get_settings
from app.core.errors import AppError
from app.infrastructure.db.session import get_db
from app.infrastructure.db.models import User
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_cookies import clear_auth_cookies, set_auth_cookies
from app.modules.identity.service.auth_service import AuthService
from app.modules.identity.service.telegram_auth_service import TelegramAuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_TELEGRAM_AUTH_STATE_COOKIE = "pv_tg_auth_state"

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


def _cookie_secure() -> bool:
    return bool(get_settings().auth_cookie_secure)


def _cookie_samesite() -> str:
    value = (get_settings().auth_cookie_samesite or "lax").lower()
    if value not in {"lax", "strict", "none"}:
        return "lax"
    return value


def _set_telegram_auth_state_cookie(response: Response, *, token: str) -> None:
    response.set_cookie(
        key=_TELEGRAM_AUTH_STATE_COOKIE,
        value=token,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        max_age=600,
        domain=get_settings().auth_cookie_domain,
        path="/",
    )


def _clear_telegram_auth_state_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_TELEGRAM_AUTH_STATE_COOKIE,
        domain=get_settings().auth_cookie_domain,
        path="/",
        secure=_cookie_secure(),
        httponly=True,
        samesite=_cookie_samesite(),
    )


def _telegram_auth_service(session: AsyncSession) -> TelegramAuthService:
    return TelegramAuthService(
        repo=UserRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        settings=get_settings(),
    )


def _site_redirect_url(path: str) -> str:
    return f"{get_settings().site_url.rstrip('/')}{path}"


def _telegram_error_reason(code: str) -> str:
    if code in {"telegram_already_linked", "telegram_account_mismatch", "conflict"}:
        return "conflict"
    if code in {"not_authenticated", "invalid_token", "invalid_telegram_auth_state"}:
        return "expired"
    if code == "telegram_login_not_configured":
        return "not_configured"
    return "failed"


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


@router.get("/telegram/start")
async def telegram_start(
    mode: str = Query(default="login", pattern="^(login|link)$"),
    next_path: str | None = Query(default=None, alias="next"),
    viewer: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    telegram_mode = "link" if mode == "link" else "login"
    if telegram_mode == "link" and viewer is None:
        raise AppError(
            code="not_authenticated",
            message="Please log in before linking Telegram.",
            status_code=401,
            message_key="errors.invalid_or_expired_token",
        )

    svc = _telegram_auth_service(session)
    state, state_token = svc.create_state_token(
        mode=telegram_mode,
        next_path=next_path,
        link_user_id=viewer.id if telegram_mode == "link" and viewer else None,
    )
    redirect = RedirectResponse(
        url=svc.build_authorization_url(state=state, state_token=state_token),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    _set_telegram_auth_state_cookie(redirect, token=state_token)
    return redirect


@router.get("/telegram/callback")
async def telegram_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> Response:
    svc = _telegram_auth_service(session)
    state_token = request.cookies.get(_TELEGRAM_AUTH_STATE_COOKIE)

    failure_mode = "login"
    failure_next_path = svc.default_next_path("login")
    if state_token:
        try:
            parsed_state = svc.decode_state_token(state_token)
            failure_mode = parsed_state.mode
            failure_next_path = parsed_state.next_path
        except AppError:
            state_token = None

    if error:
        redirect = RedirectResponse(
            url=_site_redirect_url(
                svc.callback_failure_path(
                    mode=failure_mode,
                    next_path=failure_next_path,
                    reason="cancelled" if error == "access_denied" else "failed",
                )
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        _clear_telegram_auth_state_cookie(redirect)
        return redirect

    if not code or not state or not state_token:
        redirect = RedirectResponse(
            url=_site_redirect_url(
                svc.callback_failure_path(
                    mode=failure_mode,
                    next_path=failure_next_path,
                    reason="expired",
                )
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        _clear_telegram_auth_state_cookie(redirect)
        return redirect

    try:
        result = await svc.complete_authorization(
            code=code,
            returned_state=state,
            state_token=state_token,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await session.commit()
    except AppError as exc:
        await session.rollback()
        redirect = RedirectResponse(
            url=_site_redirect_url(
                svc.callback_failure_path(
                    mode=failure_mode,
                    next_path=failure_next_path,
                    reason=_telegram_error_reason(exc.code),
                )
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        _clear_telegram_auth_state_cookie(redirect)
        return redirect

    redirect = RedirectResponse(
        url=_site_redirect_url(result.redirect_path),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _clear_telegram_auth_state_cookie(redirect)
    if result.session_tokens is not None:
        set_auth_cookies(
            redirect,
            access_token=result.session_tokens.access_token,
            refresh_token=result.session_tokens.refresh_token,
            settings=get_settings(),
        )
    return redirect


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
