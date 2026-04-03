from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_discovery_filters_cached(async_client):
    r = await async_client.get("/api/v1/prompts/discovery-filters")
    assert r.status_code == 200
    data = r.json()
    assert "difficulties" in data
    assert isinstance(data["difficulties"], list)


@pytest.mark.asyncio
async def test_billing_plans_public(async_client):
    r = await async_client.get(
        "/api/v1/billing/plans",
        headers={"Accept-Language": "en"},
    )
    assert r.status_code == 200
    plans = r.json()
    assert isinstance(plans, list)


@pytest.mark.asyncio
async def test_billing_subscription_requires_auth(async_client):
    r = await async_client.get("/api/v1/billing/subscription")
    assert r.status_code == 401
