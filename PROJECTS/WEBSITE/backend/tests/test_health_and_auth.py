from __future__ import annotations

import pytest


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
    assert "access_token" in login.json()

    out = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert out.status_code == 204


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
