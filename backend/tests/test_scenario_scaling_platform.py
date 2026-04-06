from __future__ import annotations

from datetime import datetime, timezone
import uuid

import pytest
from sqlalchemy import select

from app.infrastructure.db.models import (
    Category,
    ModerationState,
    Prompt,
    PromptStatus,
    PromptTechnique,
    User,
)
from app.infrastructure.db.session import async_session_maker


async def _register(async_client, email: str, display_name: str) -> str:
    suffix = email.split("@", 1)[0][-8:]
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "display_name": f"{display_name}-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _create_published_prompt(slug: str, *, title: str, summary: str) -> None:
    async with async_session_maker() as session:
        category = Category(
            slug=f"scale-{slug}-cat",
            name=f"Scale {slug} category",
            sort_order=0,
            is_restricted=False,
        )
        session.add(category)
        await session.flush()

        prompt = Prompt(
            slug=slug,
            title=title,
            body="Scenario body with concrete execution logic.",
            summary=summary,
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


async def _set_user_credits(email: str, credits: int) -> None:
    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.email == email.lower()))).scalar_one()
        user.mission_credits = credits
        await session.commit()


@pytest.mark.asyncio
async def test_scaling_aggregate_surfaces_present(async_client, unique_email: str):
    token = await _register(async_client, unique_email, "Scale Aggregate User")

    await _create_published_prompt(
        "scale-launch-plan",
        title="Launch plan in 24h",
        summary="Growth launch scenario for activation.",
    )
    await _create_published_prompt(
        "scale-research-brief",
        title="Research brief generator",
        summary="Research and analysis workflow scenario.",
    )
    await _create_published_prompt(
        "scale-final-review",
        title="Final review and QA",
        summary="Validation and QA scenario for shipping.",
    )

    response = await async_client.get(
        "/api/v1/scenarios/aggregate?limit=8",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["packs"], list)
    assert isinstance(payload["chains"], list)
    assert isinstance(payload["next_steps"], list)
    assert isinstance(payload["pricing_plans"], list)
    assert any(plan["tier"] == "pro" for plan in payload["pricing_plans"])


@pytest.mark.asyncio
async def test_demo_run_boost_purchase_extends_cap(async_client, unique_email: str):
    token = await _register(async_client, unique_email, "Scale Boost User")
    await _set_user_credits(unique_email, 120)

    slug = "scale-demo-cap-boost"
    await _create_published_prompt(
        slug,
        title="Demo cap with boost",
        summary="Scenario to verify token-spend demo extensions.",
    )

    for _ in range(3):
        run = await async_client.post(
            "/api/v1/scenarios/demo-run/track",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt_slug": slug, "task_input": "Base free run"},
        )
        assert run.status_code == 200
        assert run.json()["executed"] is True

    blocked = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt_slug": slug, "task_input": "Should hit cap"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["executed"] is False
    assert blocked.json()["status"]["reason"] == "free_demo_cap_reached"

    purchase = await async_client.post(
        "/api/v1/scenarios/demo-run/boost-purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt_slug": slug},
    )
    assert purchase.status_code == 200
    purchase_payload = purchase.json()
    assert purchase_payload["applied_bonus_runs"] == 3
    assert purchase_payload["bonus_runs_remaining"] >= 3

    for _ in range(3):
        boosted_run = await async_client.post(
            "/api/v1/scenarios/demo-run/track",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt_slug": slug, "task_input": "Boosted run"},
        )
        assert boosted_run.status_code == 200
        assert boosted_run.json()["executed"] is True

    blocked_again = await async_client.post(
        "/api/v1/scenarios/demo-run/track",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt_slug": slug, "task_input": "Boost exhausted"},
    )
    assert blocked_again.status_code == 200
    assert blocked_again.json()["executed"] is False
    assert blocked_again.json()["status"]["cap_reached"] is True


@pytest.mark.asyncio
async def test_blueprint_marketplace_workflow_and_team_share(async_client, unique_email: str):
    creator_email = unique_email
    consumer_email = f"consumer_{unique_email}"

    creator_token = await _register(async_client, creator_email, "Creator Scale")
    consumer_token = await _register(async_client, consumer_email, "Consumer Scale")
    await _set_user_credits(consumer_email, 120)

    create_blueprint = await async_client.post(
        "/api/v1/scenarios/studio",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "slug": "scale-creator-blueprint",
            "title": "Creator blueprint",
            "summary": "Reusable scenario blueprint for marketplace.",
            "category": "growth",
            "logic_text": "Step 1: collect context. Step 2: generate output.",
            "visibility": "marketplace",
            "is_premium": False,
        },
    )
    assert create_blueprint.status_code == 200
    blueprint = create_blueprint.json()
    blueprint_id = blueprint["id"]

    publish = await async_client.post(
        f"/api/v1/scenarios/studio/{blueprint_id}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert publish.status_code == 200
    assert publish.json()["blueprint"]["is_published"] is True

    marketplace = await async_client.get("/api/v1/scenarios/marketplace?limit=12")
    assert marketplace.status_code == 200
    assert any(item["id"] == blueprint_id for item in marketplace.json())

    fork = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/fork",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert fork.status_code == 200
    fork_payload = fork.json()
    forked_id = fork_payload["forked_blueprint"]["id"]

    like = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/like",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert like.status_code == 200
    assert like.json()["like_count"] >= 1

    workflow = await async_client.post(
        "/api/v1/scenarios/workflows",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={
            "name": "Scale workflow",
            "description": "Forked blueprint workflow",
            "visibility": "private",
            "step_blueprint_ids": [forked_id],
        },
    )
    assert workflow.status_code == 200
    workflow_id = workflow.json()["id"]

    run = await async_client.post(
        f"/api/v1/scenarios/workflows/{workflow_id}/run",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={"context": {"job": "ship"}},
    )
    assert run.status_code == 200
    run_id = run.json()["id"]

    advanced = await async_client.post(
        f"/api/v1/scenarios/workflows/runs/{run_id}/advance",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert advanced.status_code == 200
    assert advanced.json()["is_completed"] is True

    share = await async_client.post(
        f"/api/v1/scenarios/studio/{blueprint_id}/share",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_email": consumer_email, "can_edit": True},
    )
    assert share.status_code == 200
    assert share.json()["can_edit"] is True

    shared = await async_client.get(
        "/api/v1/scenarios/team/shared",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert shared.status_code == 200
    assert any(item["id"] == blueprint_id for item in shared.json())


@pytest.mark.asyncio
async def test_showcase_share_and_upvote(async_client, unique_email: str):
    author_email = unique_email
    voter_email = f"voter_{unique_email}"

    author_token = await _register(async_client, author_email, "Showcase Author")
    voter_token = await _register(async_client, voter_email, "Showcase Voter")

    share = await async_client.post(
        "/api/v1/scenarios/showcase/share",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "title": "Generated onboarding map",
            "excerpt": "Reduced onboarding friction and improved first-run activation.",
            "output_preview": "Output: sequence of onboarding actions with retention triggers.",
            "prompt_slug": "showcase-demo-slug",
            "visibility": "public",
        },
    )
    assert share.status_code == 200
    share_payload = share.json()
    share_id = share_payload["share_id"]

    upvote = await async_client.post(
        "/api/v1/scenarios/showcase/upvote",
        headers={"Authorization": f"Bearer {voter_token}"},
        json={"share_id": share_id},
    )
    assert upvote.status_code == 200
    assert upvote.json()["upvotes"] >= 1


@pytest.mark.asyncio
async def test_marketplace_discovery_social_and_lineage_v4(async_client, unique_email: str):
    creator_email = unique_email
    consumer_email = f"consumer_v4_{unique_email}"

    creator_token = await _register(async_client, creator_email, "Creator V4")
    consumer_token = await _register(async_client, consumer_email, "Consumer V4")
    await _set_user_credits(consumer_email, 240)

    create_blueprint = await async_client.post(
        "/api/v1/scenarios/studio",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "slug": "v4-market-os",
            "title": "V4 Market OS",
            "summary": "Creator operating system for scenario growth loop.",
            "category": "growth",
            "tags": ["growth", "onboarding", "retention"],
            "visibility": "premium",
            "monetization_mode": "paid",
            "token_price": 20,
            "logic_text": "1. Capture context. 2. Generate response. 3. Validate and publish.",
        },
    )
    assert create_blueprint.status_code == 200
    blueprint_id = create_blueprint.json()["id"]

    patch_blueprint = await async_client.patch(
        f"/api/v1/scenarios/studio/{blueprint_id}",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"summary": "Updated summary for version two."},
    )
    assert patch_blueprint.status_code == 200
    assert patch_blueprint.json()["version_number"] >= 2

    publish = await async_client.post(
        f"/api/v1/scenarios/studio/{blueprint_id}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert publish.status_code == 200
    assert publish.json()["blueprint"]["is_published"] is True

    discovery = await async_client.get(
        "/api/v1/scenarios/marketplace?section=trending&search=v4&category=growth&limit=12",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert discovery.status_code == 200
    discovered = discovery.json()
    assert any(item["id"] == blueprint_id for item in discovered)

    rate = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/rating",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={"rating": 5},
    )
    assert rate.status_code == 200
    assert rate.json()["rating_count"] >= 1

    comment = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/comments",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={"body": "Great creator scenario, clear loop and remix value."},
    )
    assert comment.status_code == 200

    save = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/save",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert save.status_code == 200
    assert save.json()["saved"] is True

    run_event = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/usage",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={"event": "run"},
    )
    assert run_event.status_code == 200
    complete_event = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/usage",
        headers={"Authorization": f"Bearer {consumer_token}"},
        json={"event": "complete"},
    )
    assert complete_event.status_code == 200
    assert complete_event.json()["completion_count"] >= 1

    remix = await async_client.post(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/remix",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert remix.status_code == 200
    remixed_id = remix.json()["forked_blueprint"]["id"]

    lineage = await async_client.get(
        f"/api/v1/scenarios/studio/{remixed_id}/lineage",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert lineage.status_code == 200
    lineage_payload = lineage.json()
    assert len(lineage_payload["chain"]) >= 1

    versions = await async_client.get(
        f"/api/v1/scenarios/studio/{blueprint_id}/versions?limit=12",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert versions.status_code == 200
    assert len(versions.json()) >= 2

    comments = await async_client.get(
        f"/api/v1/scenarios/marketplace/{blueprint_id}/comments?limit=20",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert comments.status_code == 200
    assert any("remix value" in item["body"] for item in comments.json())


@pytest.mark.asyncio
async def test_autonomous_v5_loop_runs_end_to_end(async_client, unique_email: str):
    token = await _register(async_client, unique_email, "Autonomy Operator")

    now = datetime.now(timezone.utc)
    ingest = await async_client.post(
        "/api/v1/analytics/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "events": [
                {
                    "event_id": f"auto-signup-{uuid.uuid4().hex[:12]}",
                    "event_name": "signup_completed",
                    "session_id": "auto-session-v5",
                    "timestamp": now.isoformat(),
                    "context": {"page": "/autonomy", "feature": "test"},
                    "metadata": {"source": "organic"},
                },
                {
                    "event_id": f"auto-run-{uuid.uuid4().hex[:12]}",
                    "event_name": "scenario_run",
                    "session_id": "auto-session-v5",
                    "timestamp": now.isoformat(),
                    "context": {"page": "/autonomy", "feature": "test"},
                    "metadata": {"status": "failed", "intent": "retention rescue"},
                },
                {
                    "event_id": f"auto-search-{uuid.uuid4().hex[:12]}",
                    "event_name": "catalog_search_used",
                    "session_id": "auto-session-v5",
                    "timestamp": now.isoformat(),
                    "context": {"page": "/autonomy", "feature": "test"},
                    "metadata": {"query": "improve retention in onboarding"},
                },
            ]
        },
    )
    assert ingest.status_code == 202

    run = await async_client.post(
        "/api/v1/scenarios/autonomy/run",
        headers={"Authorization": f"Bearer {token}"},
        json={"force": True, "max_new_scenarios": 2},
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["generated_count"] >= 1
    assert payload["published_count"] >= 1
    assert isinstance(payload["experiments"], list)
    assert len(payload["experiments"]) >= 1
    assert payload["self_check"]["creates_new_scenarios"] is True
    assert payload["self_check"]["tests_autonomously"] is True

    status = await async_client.get(
        "/api/v1/scenarios/autonomy/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["enabled"] is True
    assert status_payload["latest_cycle"] is not None

    self_check = await async_client.get(
        "/api/v1/scenarios/autonomy/self-check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert self_check.status_code == 200
    assert self_check.json()["creates_new_scenarios"] is True

    personalization = await async_client.get(
        "/api/v1/scenarios/autonomy/personalization",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert personalization.status_code == 200
    personalization_payload = personalization.json()
    assert personalization_payload["ui_variant"] in {"control", "guided"}
    assert isinstance(personalization_payload["recommended_blueprints"], list)
