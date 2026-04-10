from __future__ import annotations

import pytest


def _set_cookie_headers(response) -> list[str]:
    return response.headers.get_list("set-cookie")


@pytest.mark.asyncio
async def test_health_ok(async_client):
    r = await async_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_login_me_logout(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Pytest User",
        },
    )
    assert reg.status_code == 201
    reg_set_cookies = _set_cookie_headers(reg)
    assert any("pv_auth_state=1" in header for header in reg_set_cookies)
    body = reg.json()
    assert "access_token" in body
    token = body["access_token"]

    me = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == unique_email.lower()

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    assert login.status_code == 200
    login_set_cookies = _set_cookie_headers(login)
    assert any("pv_auth_state=1" in header for header in login_set_cookies)
    assert "access_token" in login.json()

    out = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert out.status_code == 204
    logout_set_cookies = _set_cookie_headers(out)
    assert any("pv_auth_state=" in header and "Max-Age=0" in header for header in logout_set_cookies)


@pytest.mark.asyncio
async def test_me_requires_auth(async_client):
    r = await async_client.get("/api/v1/users/me")
    assert r.status_code == 401
    data = r.json()
    assert data.get("code") in {"not_authenticated", "invalid_token"}


@pytest.mark.asyncio
async def test_invalid_credentials(async_client, unique_email: str):
    r = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "wrong-password"},
    )
    assert r.status_code == 401
    assert r.json().get("code") == "invalid_credentials"


@pytest.mark.asyncio
async def test_register_rejects_duplicate_display_name_case_insensitive(async_client, unique_email: str):
    first = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Prompts Vault Team",
        },
    )
    assert first.status_code == 201

    second = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email.replace("@", ".other@"),
            "password": "password123",
            "display_name": "prompts vault team",
        },
    )
    assert second.status_code == 409
    assert second.json().get("code") == "conflict"


@pytest.mark.asyncio
async def test_update_me_rejects_duplicate_display_name(async_client, unique_email: str):
    first = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Nickname Alpha",
        },
    )
    assert first.status_code == 201

    second = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email.replace("@", ".second@"),
            "password": "password123",
            "display_name": "Nickname Beta",
        },
    )
    assert second.status_code == 201

    patch = await async_client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {second.json()['access_token']}"},
        json={"display_name": "nickname alpha"},
    )
    assert patch.status_code == 409
    assert patch.json().get("code") == "conflict"
