from __future__ import annotations

import pytest

from app.infrastructure.db.models import LessonMission, MissionActionType, MissionProgressStatus
from app.modules.missions.service.mission_service import MissionService


@pytest.mark.asyncio
async def test_onboarding_requires_auth(async_client):
    r = await async_client.get("/api/v1/onboarding/profile")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_missions_requires_auth(async_client):
    r = await async_client.get("/api/v1/missions")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_missions_list_returns_for_user(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Mission User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    r = await async_client.get(
        "/api/v1/missions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "missions" in body
    assert "total_count" in body


def test_completed_mission_next_step_points_to_mission_result():
    service = MissionService(repo=None, onboarding_repo=None, prompt_repo=None)  # type: ignore[arg-type]
    mission = LessonMission(
        slug="first-win",
        title="First win",
        description=None,
        objective="Do one task",
        completion_condition="Complete one event",
        action_type=MissionActionType.manual_confirmation,
        required_count=1,
        is_active=True,
        sort_order=1,
    )

    next_step = service._mission_next_step(
        mission,
        prompts=[],
        lesson=None,
        status=MissionProgressStatus.completed,
    )

    assert next_step is not None
    assert next_step.label == "View result"
    assert next_step.href == "/missions/first-win"
    assert next_step.action == "view_result"
