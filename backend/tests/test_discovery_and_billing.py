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


@pytest.mark.asyncio
async def test_categories_localized_and_cache_is_language_aware(async_client):
    def category_name(rows: list[dict], slug: str) -> str:
        entry = next((item for item in rows if item.get("slug") == slug), None)
        assert entry is not None, f"Category {slug} should exist"
        return str(entry["name"])

    en_first = await async_client.get("/api/v1/categories", headers={"Accept-Language": "en"})
    ru = await async_client.get("/api/v1/categories", headers={"Accept-Language": "ru"})
    en_second = await async_client.get("/api/v1/categories", headers={"Accept-Language": "en"})

    assert en_first.status_code == 200
    assert ru.status_code == 200
    assert en_second.status_code == 200

    en_first_name = category_name(en_first.json(), "it")
    ru_name = category_name(ru.json(), "it")
    en_second_name = category_name(en_second.json(), "it")

    assert en_first_name == "Information Technology and Software Development"
    assert ru_name == "Информационные технологии и разработка ПО"
    assert en_second_name == "Information Technology and Software Development"
