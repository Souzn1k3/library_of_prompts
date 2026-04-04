"""Mock billing checkout (BILLING_MOCK_MODE) — end-to-end tier transition without Stripe API calls."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_mock_checkout_session_upgrades_plan_tier(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": f"Billing User {unique_email.split('@', 1)[0][-8:]}",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    checkout = await async_client.post(
        "/api/v1/billing/checkout/session",
        headers={"Authorization": f"Bearer {token}"},
        json={"tier": "starter"},
    )
    assert checkout.status_code == 200
    data = checkout.json()
    assert "url" in data
    assert "session_id" in data

    me = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["plan_tier"] == "starter"

    sub = await async_client.get(
        "/api/v1/billing/subscription",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sub.status_code == 200
    body = sub.json()
    assert body.get("plan_tier") == "starter"
    assert body.get("status") == "active"


@pytest.mark.asyncio
async def test_mock_checkout_rejects_external_redirect_url(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": f"Billing User {unique_email.split('@', 1)[0][-8:]}",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    checkout = await async_client.post(
        "/api/v1/billing/checkout/session",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tier": "starter",
            "success_url": "https://evil.example/checkout/complete",
        },
    )
    assert checkout.status_code == 400
    assert checkout.json()["code"] == "invalid_redirect_url"


@pytest.mark.asyncio
async def test_mock_billing_portal_rejects_external_return_url(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": f"Billing User {unique_email.split('@', 1)[0][-8:]}",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    portal = await async_client.post(
        "/api/v1/billing/portal",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "return_url": "https://evil.example/account",
        },
    )
    assert portal.status_code == 400
    assert portal.json()["code"] == "invalid_redirect_url"


