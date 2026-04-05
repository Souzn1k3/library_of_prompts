from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from app.modules.catalog.service.prompt_engagement_service import PromptEngagementService
from app.modules.economy.model.store import EconomyActionRead


@dataclass
class _WalletStub:
    balance: int


@dataclass
class _UserStub:
    id: uuid.UUID


class _PromptStub:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, _UserStub | None]] = []

    async def track_copy(self, prompt_id: uuid.UUID, viewer: _UserStub | None) -> None:
        self.calls.append((prompt_id, viewer))


class _MissionStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def record_event(self, **kwargs: Any) -> list[str]:
        self.calls.append(kwargs)
        event_type = str(kwargs["event_type"])
        return [f"{event_type}:done"]


class _ContributorStub:
    def __init__(self) -> None:
        self.prompt_ids: list[uuid.UUID] = []

    async def refresh_prompt_quality(self, prompt_id: uuid.UUID) -> None:
        self.prompt_ids.append(prompt_id)


class _StoreStub:
    def __init__(self) -> None:
        self.wallet_calls: list[_UserStub] = []
        self.feedback_calls: list[dict[str, Any]] = []

    async def wallet(self, user: _UserStub) -> _WalletStub:
        self.wallet_calls.append(user)
        return _WalletStub(balance=120)

    async def build_action_feedback(
        self,
        user: _UserStub,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead:
        self.feedback_calls.append(
            {
                "user": user,
                "previous_balance": previous_balance,
                "completed_mission_slugs": list(completed_mission_slugs or []),
            }
        )
        return EconomyActionRead(
            balance=130,
            balance_delta=10,
            completed_mission_slugs=list(completed_mission_slugs or []),
        )


class _CacheStub:
    def __init__(self) -> None:
        self.bump_many_calls: list[tuple[str, ...]] = []

    async def bump_many(self, namespaces: list[str] | tuple[str, ...]) -> None:
        self.bump_many_calls.append(tuple(namespaces))


@pytest.mark.asyncio
async def test_track_copy_anonymous_refreshes_quality_and_cache() -> None:
    prompts = _PromptStub()
    missions = _MissionStub()
    contributors = _ContributorStub()
    store = _StoreStub()
    cache = _CacheStub()
    service = PromptEngagementService(
        prompts=prompts,
        missions=missions,
        contributors=contributors,
        store=store,
        cache=cache,
    )

    prompt_id = uuid.uuid4()
    result = await service.track_copy(prompt_id=prompt_id, viewer=None)

    assert isinstance(result, EconomyActionRead)
    assert prompts.calls == [(prompt_id, None)]
    assert contributors.prompt_ids == [prompt_id]
    assert cache.bump_many_calls == [("prompts", "contributors", "recommendations")]
    assert store.wallet_calls == []
    assert store.feedback_calls == []
    assert missions.calls == []


@pytest.mark.asyncio
async def test_track_copy_authenticated_records_events_and_feedback() -> None:
    prompts = _PromptStub()
    missions = _MissionStub()
    contributors = _ContributorStub()
    store = _StoreStub()
    cache = _CacheStub()
    service = PromptEngagementService(
        prompts=prompts,
        missions=missions,
        contributors=contributors,
        store=store,
        cache=cache,
    )

    user = _UserStub(id=uuid.uuid4())
    prompt_id = uuid.uuid4()
    result = await service.track_copy(prompt_id=prompt_id, viewer=user)

    assert result.balance == 130
    assert prompts.calls == [(prompt_id, user)]
    assert contributors.prompt_ids == [prompt_id]
    assert len(missions.calls) == 2
    assert missions.calls[0]["event_type"] == "prompt_copied"
    assert missions.calls[1]["event_type"] == "streak_activity"
    assert store.wallet_calls == [user]
    assert store.feedback_calls[0]["previous_balance"] == 120
    assert store.feedback_calls[0]["completed_mission_slugs"] == [
        "prompt_copied:done",
        "streak_activity:done",
    ]
    assert cache.bump_many_calls == [("prompts", "contributors", "recommendations")]


@pytest.mark.asyncio
async def test_track_apply_anonymous_is_noop() -> None:
    service = PromptEngagementService(
        prompts=_PromptStub(),
        missions=_MissionStub(),
        contributors=_ContributorStub(),
        store=_StoreStub(),
        cache=_CacheStub(),
    )

    result = await service.track_apply(prompt_id=uuid.uuid4(), viewer=None)

    assert result == EconomyActionRead()


@pytest.mark.asyncio
async def test_track_apply_authenticated_records_progress_feedback() -> None:
    missions = _MissionStub()
    store = _StoreStub()
    service = PromptEngagementService(
        prompts=_PromptStub(),
        missions=missions,
        contributors=_ContributorStub(),
        store=store,
        cache=_CacheStub(),
    )
    user = _UserStub(id=uuid.uuid4())
    prompt_id = uuid.uuid4()

    result = await service.track_apply(prompt_id=prompt_id, viewer=user)

    assert result.balance_delta == 10
    assert len(missions.calls) == 2
    assert missions.calls[0]["event_type"] == "prompt_applied"
    assert missions.calls[1]["event_type"] == "streak_activity"
    assert store.feedback_calls[0]["completed_mission_slugs"] == [
        "prompt_applied:done",
        "streak_activity:done",
    ]
