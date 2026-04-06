from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.infrastructure.db.models import Category, ModerationState, Prompt, PromptStatus, PromptTechnique
from app.infrastructure.db.session import async_session_maker


async def _register(async_client, email: str, display_name: str = "Scenario User") -> str:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _create_published_prompt(slug: str) -> None:
    async with async_session_maker() as session:
        category = Category(
            slug=f"scenario-{slug}-cat",
            name=f"Scenario {slug} category",
            sort_order=0,
            is_restricted=False,
        )
        session.add(category)
        await session.flush()

        prompt = Prompt(
            slug=slug,
            title=f"Scenario {slug}",
            body="Do the scenario with execution steps.",
            summary="Scenario summary for testing.",
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


@pytest.mark.asyncio
async def test_scenario_workspace_is_server_synced(async_client, unique_email: str):
    token = await _register(async_client, unique_email)
    slug = "scenario-workspace-server-synced"
    await _create_published_prompt(slug)

    run_response = await async_client.post(
        "/api/v1/scenarios/workspace/track",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt_slug": slug,
            "action": "run",
            "task_input": "Build migration-safe rollout plan",
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["action"] == "run"
    assert payload["workspace"]["unfinished"][0]["prompt"]["slug"] == slug

    read_response = await async_client.get(
        "/api/v1/scenarios/workspace",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert read_response.status_code == 200
    workspace = read_response.json()

    assert any(item["prompt"]["slug"] == slug for item in workspace["recent"])
    assert any(item["prompt"]["slug"] == slug for item in workspace["unfinished"])

    save_response = await async_client.post(
        "/api/v1/scenarios/workspace/track",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt_slug": slug,
            "action": "save",
        },
    )
    assert save_response.status_code == 200

    workspace_after_save = await async_client.get(
        "/api/v1/scenarios/workspace",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workspace_after_save.status_code == 200
    data = workspace_after_save.json()
    assert any(item["prompt"]["slug"] == slug for item in data["saved"])


@pytest.mark.asyncio
async def test_scenario_home_aggregate_includes_workspace_for_authenticated_user(async_client, unique_email: str):
    token = await _register(async_client, unique_email, display_name="Aggregate User")
    slug = "scenario-aggregate-proof"
    await _create_published_prompt(slug)

    track_response = await async_client.post(
        "/api/v1/scenarios/workspace/track",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt_slug": slug,
            "action": "open",
            "task_input": "Return to this scenario after navigation",
        },
    )
    assert track_response.status_code == 200

    aggregate_response = await async_client.get(
        "/api/v1/scenarios/aggregate?limit=6",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert aggregate_response.status_code == 200
    aggregate = aggregate_response.json()

    assert aggregate["workspace"] is not None
    assert "core_loop_steps" in aggregate["loop_hints"]
    assert aggregate["workspace_limits"]["recent_limit"] >= 1
    assert any(item["prompt"]["slug"] == slug for item in aggregate["workspace"]["recent"])
