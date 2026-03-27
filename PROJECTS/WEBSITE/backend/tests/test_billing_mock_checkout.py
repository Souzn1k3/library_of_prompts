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
            "display_name": "Billing User",
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
