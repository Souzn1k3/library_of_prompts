from __future__ import annotations

import hashlib
import uuid

from fastapi import Request, Response

from app.config import Settings

GUEST_SESSION_COOKIE = "pv_guest_sid"
GUEST_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 90


def _cookie_samesite(settings: Settings) -> str:
    value = (settings.auth_cookie_samesite or "lax").lower()
    if value not in {"lax", "strict", "none"}:
        return "lax"
    return value


def get_or_set_guest_session_id(*, request: Request, response: Response, settings: Settings) -> str:
    existing = request.cookies.get(GUEST_SESSION_COOKIE, "").strip()
    if existing and len(existing) <= 80:
        return existing

    generated = uuid.uuid4().hex
    response.set_cookie(
        key=GUEST_SESSION_COOKIE,
        value=generated,
        httponly=True,
        secure=bool(settings.auth_cookie_secure),
        samesite=_cookie_samesite(settings),
        max_age=GUEST_SESSION_MAX_AGE_SECONDS,
        domain=settings.auth_cookie_domain,
        path="/",
    )
    return generated


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def request_ip_hash(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        raw_ip = xff.split(",")[0].strip()
    else:
        client = request.client
        raw_ip = client.host if client else "unknown"
    return sha256_hex(raw_ip or "unknown")


def request_user_agent_hash(request: Request) -> str:
    return sha256_hex(request.headers.get("user-agent", "unknown-agent"))


def request_device_fingerprint_hash(request: Request) -> str:
    # Pragmatic (not tamper-proof) fingerprint baseline for guest anti-abuse.
    parts = [
        request.headers.get("user-agent", ""),
        request.headers.get("accept-language", ""),
        request.headers.get("sec-ch-ua", ""),
        request.headers.get("sec-ch-ua-platform", ""),
        request.headers.get("sec-ch-ua-mobile", ""),
    ]
    canonical = "|".join(part.strip().lower()[:180] for part in parts)
    return sha256_hex(canonical or "unknown-fingerprint")
