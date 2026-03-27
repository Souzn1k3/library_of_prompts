from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_discovery_sections_include_for_you_bucket(async_client):
    response = await async_client.get("/api/v1/prompts/discovery-sections")
    assert response.status_code == 200
    data = response.json()
    assert "for_you" in data
    assert isinstance(data["for_you"], list)


@pytest.mark.asyncio
async def test_related_prompts_exclude_seed(async_client):
    prompt_response = await async_client.get("/api/v1/prompts?limit=3")
    assert prompt_response.status_code == 200
    prompts = prompt_response.json()
    if not prompts:
        pytest.skip("Seed prompts unavailable for recommendation test")

    seed_slug = prompts[0]["slug"]
    response = await async_client.get(f"/api/v1/prompts/by-slug/{seed_slug}/related?limit=4")
    assert response.status_code == 200
    related = response.json()
    assert all(item["slug"] != seed_slug for item in related)
    if related:
        assert related[0]["recommendation_reason_key"]


@pytest.mark.asyncio
async def test_dashboard_recommendations_respect_saved_history(async_client, unique_email: str):
    registration = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Recommendation User",
        },
    )
    assert registration.status_code == 201
    token = registration.json()["access_token"]

    prompts_response = await async_client.get("/api/v1/prompts?limit=4")
    assert prompts_response.status_code == 200
    prompts = prompts_response.json()
    if len(prompts) < 2:
        pytest.skip("Need at least two prompts to validate personalized recommendations")

    saved_prompt_id = prompts[0]["id"]
    save_response = await async_client.post(
        f"/api/v1/users/me/saved-prompts/{saved_prompt_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert save_response.status_code == 204

    recommendation_response = await async_client.get(
        "/api/v1/prompts/recommendations?context=dashboard&limit=4",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert recommendation_response.status_code == 200
    payload = recommendation_response.json()
    assert payload["context"] == "dashboard"
    assert isinstance(payload["items"], list)
    if payload["items"]:
        assert all(item["id"] != saved_prompt_id for item in payload["items"])
        assert any(item.get("recommendation_reason_key") for item in payload["items"])
