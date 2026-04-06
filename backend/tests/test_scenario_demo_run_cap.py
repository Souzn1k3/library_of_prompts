from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.infrastructure.db.models import Category, ModerationState, PlanTier, Prompt, PromptStatus, PromptTechnique, User
from app.infrastructure.db.session import async_session_maker


async def _register(async_client, email: str, display_name: str = "Scenario Cap User") -> str:
    unique_display_name = f"{display_name}-{email.split('@', 1)[0][-8:]}"
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "display_name": unique_display_name,
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _create_published_prompt(slug: str) -> None:
    async with async_session_maker() as session:
        category = Category(
            slug=f"cap-{slug}-cat",
            name=f"Cap {slug} category",
            sort_order=0,
            is_restricted=False,
        )
        session.add(category)
        await session.flush()

        prompt = Prompt(
            slug=slug,
            title=f"Cap {slug}",
            body="Do the scenario with execution steps.",
            summary="Scenario summary for cap tests.",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            is_premium=False,
            category_id=category.id,
            author_id=None,
            auto_approved=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(prompt)
        await session.commit()


async def _set_plan(email: str, tier: PlanTier) -> None:
    async with async_session_maker() as session:
        user = (
            await session.execute(select(User).where(User.email == email.lower()))
        ).scalar_one()
        user.plan_tier = tier
        await session.commit()


@pytest.mark.asyncio
async def test_demo_run_limit_and_cap_for_free_user(async_client, unique_email: str):
    token = await _register(async_client, unique_email)
    slug = "demo-cap-free-user"
    await _create_published_prompt(slug)

    for expected_used in (1, 2, 3):
        response = await async_client.post(
            "/api/v1/scenarios/demo-run/track",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt_slug": slug, "task_input": "Ship a launch checklist"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["executed"] is True
        assert payload["status"]["used_runs"] == expected_used
        assert payload["status"]["free_cap"] == 3

    reached = await async_client.get(
        f"/api/v1/scenarios/demo-run/status?prompt_slug={slug}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reached.status_code == 200
    reached_payload = reached.json()
    assert reached_payload["cap_reached"] is True
    assert reached_payload["remaining_runs"] == 0

    exceeded = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt_slug": slug, "task_input": "Try to bypass"},
    )
    assert exceeded.status_code == 200
    exceeded_payload = exceeded.json()
    assert exceeded_payload["executed"] is False
    assert exceeded_payload["status"]["cap_reached"] is True
    assert exceeded_payload["status"]["reason"] == "free_demo_cap_reached"


@pytest.mark.asyncio
async def test_demo_run_pro_user_bypasses_free_cap(async_client, unique_email: str):
    token = await _register(async_client, unique_email)
    await _set_plan(unique_email, PlanTier.pro)
    slug = "demo-cap-pro-user"
    await _create_published_prompt(slug)

    for _ in range(5):
        response = await async_client.post(
            "/api/v1/scenarios/demo-run/track",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt_slug": slug, "task_input": "Run without free cap"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["executed"] is True
        assert payload["status"]["is_pro"] is True
        assert payload["status"]["free_cap"] is None
        assert payload["status"]["cap_reached"] is False


@pytest.mark.asyncio
async def test_demo_run_guest_persists_after_reload_and_respects_cap(async_client):
    slug = "demo-cap-guest-user"
    await _create_published_prompt(slug)

    first = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        json={"prompt_slug": slug, "task_input": "Guest run"},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["executed"] is True
    assert first_payload["status"]["is_authenticated"] is False
    assert first_payload["status"]["used_runs"] == 1
    assert first_payload["status"]["guest_session_id"]

    second = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        json={"prompt_slug": slug, "task_input": "Guest run 2"},
    )
    assert second.status_code == 200
    assert second.json()["status"]["used_runs"] == 2

    status_after_reload = await async_client.get(f"/api/v1/scenarios/demo-run/status?prompt_slug={slug}")
    assert status_after_reload.status_code == 200
    status_payload = status_after_reload.json()
    assert status_payload["used_runs"] == 2
    assert status_payload["remaining_runs"] == 1

    third = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        json={"prompt_slug": slug, "task_input": "Guest run 3"},
    )
    assert third.status_code == 200
    assert third.json()["executed"] is True
    assert third.json()["status"]["used_runs"] == 3

    blocked = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        json={"prompt_slug": slug, "task_input": "Guest run 4"},
    )
    assert blocked.status_code == 200
    blocked_payload = blocked.json()
    assert blocked_payload["executed"] is False
    assert blocked_payload["status"]["cap_reached"] is True
    assert blocked_payload["status"]["remaining_runs"] == 0
