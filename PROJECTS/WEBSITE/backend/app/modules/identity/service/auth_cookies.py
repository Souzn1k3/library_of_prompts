from datetime import timedelta

from fastapi import Response

from app.config import Settings


def _cookie_secure(settings: Settings) -> bool:
    return bool(settings.auth_cookie_secure)


def _cookie_samesite(settings: Settings) -> str:
    value = (settings.auth_cookie_samesite or "lax").lower()
    if value not in {"lax", "strict", "none"}:
        return "lax"
    return value


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    settings: Settings,
) -> None:
    secure = _cookie_secure(settings)
    samesite = _cookie_samesite(settings)
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds()),
        domain=settings.auth_cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
        domain=settings.auth_cookie_domain,
        path="/",
    )


def clear_auth_cookies(response: Response, *, settings: Settings) -> None:
    secure = _cookie_secure(settings)
    samesite = _cookie_samesite(settings)
    response.delete_cookie(
        key=settings.access_token_cookie_name,
        domain=settings.auth_cookie_domain,
        path="/",
        secure=secure,
        httponly=True,
        samesite=samesite,
    )
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        domain=settings.auth_cookie_domain,
        path="/",
        secure=secure,
        httponly=True,
        samesite=samesite,
    )

