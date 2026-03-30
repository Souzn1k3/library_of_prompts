from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_store_list_returns_seeded_items(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Store User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    response = await async_client.get(
        "/api/v1/store",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data


@pytest.mark.asyncio
async def test_store_purchase_rejects_too_long_client_token(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Store User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    response = await async_client.post(
        "/api/v1/store/pro-trial-pass/purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_token": "x" * 81},
    )
    assert response.status_code == 422
