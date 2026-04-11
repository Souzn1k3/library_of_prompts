from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import async_session_maker
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.telegram_auth_service import TelegramAuthService

_STATE_COOKIE_NAME = "pv_tg_auth_state"


def _set_cookie_headers(response) -> list[str]:
    return response.headers.get_list("set-cookie")


async def _build_state_token(
    *,
    mode: str,
    next_path: str,
    link_user_id: uuid.UUID | None = None,
) -> tuple[str, str]:
    async with async_session_maker() as session:
        svc = TelegramAuthService(
            repo=UserRepository(session),
            refresh_tokens=RefreshTokenRepository(session),
            settings=get_settings(),
        )
        return svc.create_state_token(
            mode="link" if mode == "link" else "login",
            next_path=next_path,
            link_user_id=None if link_user_id is None else link_user_id,
        )


async def _get_user_by_telegram_user_id(telegram_user_id: int) -> User | None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_telegram_start_redirects_to_provider(async_client):
    response = await async_client.get("/api/v1/auth/telegram/start")

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://oauth.telegram.org/auth?")
    assert "client_id=pytest-telegram-client-id" in location
    assert "scope=openid+profile" in location
    assert "code_challenge_method=S256" in location
    assert "redirect_uri=http%3A%2F%2Ftest%2Fapi%2Fv1%2Fauth%2Ftelegram%2Fcallback" in location

    set_cookies = _set_cookie_headers(response)
    assert any(_STATE_COOKIE_NAME in header for header in set_cookies)


@pytest.mark.asyncio
async def test_telegram_callback_creates_user_and_sets_auth_cookies(async_client, monkeypatch):
    async def fake_exchange(self, *, code: str, code_verifier: str) -> dict[str, str]:
        assert code == "code-1"
        assert code_verifier
        return {"id_token": "telegram-id-token"}

    async def fake_verify(self, id_token: str) -> dict[str, object]:
        assert id_token == "telegram-id-token"
        return {
            "id": 77001,
            "sub": "77001",
            "username": "tg_login_user",
            "first_name": "Tele",
            "last_name": "Gram",
            "language_code": "ru",
        }

    monkeypatch.setattr(TelegramAuthService, "_exchange_code_for_tokens", fake_exchange)
    monkeypatch.setattr(TelegramAuthService, "_verify_id_token", fake_verify)

    state, state_token = await _build_state_token(mode="login", next_path="/dashboard")
    async_client.cookies.set(_STATE_COOKIE_NAME, state_token)

    response = await async_client.get(
        "/api/v1/auth/telegram/callback",
        params={"code": "code-1", "state": state},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "http://127.0.0.1:3000/dashboard"

    set_cookies = _set_cookie_headers(response)
    assert any("pv_access_token=" in header for header in set_cookies)
    assert any("pv_refresh_token=" in header for header in set_cookies)
    assert any("pv_auth_state=1" in header for header in set_cookies)

    user = await _get_user_by_telegram_user_id(77001)
    assert user is not None
    assert user.email == "tg_77001@telegram.local"
    assert user.telegram_username == "tg_login_user"
    assert user.display_name == "Tele Gram"


@pytest.mark.asyncio
async def test_telegram_callback_links_existing_user(async_client, unique_email: str, monkeypatch):
    register = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Existing User",
        },
    )
    assert register.status_code == 201

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == unique_email.lower()))
        user = result.scalar_one()
        link_user_id = user.id

    async def fake_exchange(self, *, code: str, code_verifier: str) -> dict[str, str]:
        assert code == "code-2"
        assert code_verifier
        return {"id_token": "telegram-link-token"}

    async def fake_verify(self, id_token: str) -> dict[str, object]:
        assert id_token == "telegram-link-token"
        return {
            "id": 88002,
            "sub": "88002",
            "username": "linked_user",
            "first_name": "Linked",
            "last_name": "User",
            "language_code": "ru",
        }

    monkeypatch.setattr(TelegramAuthService, "_exchange_code_for_tokens", fake_exchange)
    monkeypatch.setattr(TelegramAuthService, "_verify_id_token", fake_verify)

    state, state_token = await _build_state_token(mode="link", next_path="/profile", link_user_id=link_user_id)
    async_client.cookies.set(_STATE_COOKIE_NAME, state_token)

    response = await async_client.get(
        "/api/v1/auth/telegram/callback",
        params={"code": "code-2", "state": state},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "http://127.0.0.1:3000/profile?telegram=linked"

    async with async_session_maker() as session:
        linked_user = await session.get(User, link_user_id)
        assert linked_user is not None
        assert linked_user.telegram_user_id == 88002
        assert linked_user.telegram_username == "linked_user"
