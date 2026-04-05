from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Protocol

from app.infrastructure.db.models import User
from app.modules.economy.model.store import EconomyActionRead


class PromptServiceProtocol(Protocol):
    async def track_copy(self, prompt_id: uuid.UUID, viewer: User | None) -> None: ...


class MissionServiceProtocol(Protocol):
    async def record_event(
        self,
        *,
        user: User,
        event_type: str,
        prompt_id: uuid.UUID | None = None,
        lesson_id: uuid.UUID | None = None,
        source_event_key: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> list[str]: ...


class ContributorServiceProtocol(Protocol):
    async def refresh_prompt_quality(self, prompt_id: uuid.UUID) -> None: ...


class StoreServiceProtocol(Protocol):
    async def wallet(self, user: User): ...

    async def build_action_feedback(
        self,
        user: User,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead: ...


class CacheInvalidatorProtocol(Protocol):
    async def bump_many(self, namespaces: list[str] | tuple[str, ...]) -> None: ...


class PromptEngagementService:
    def __init__(
        self,
        *,
        prompts: PromptServiceProtocol,
        missions: MissionServiceProtocol,
        contributors: ContributorServiceProtocol,
        store: StoreServiceProtocol,
        cache: CacheInvalidatorProtocol | None = None,
    ) -> None:
        self._prompts = prompts
        self._missions = missions
        self._contributors = contributors
        self._store = store
        self._cache = cache

    async def _bump_prompt_caches(self) -> None:
        if self._cache is None:
            return
        await self._cache.bump_many(("prompts", "contributors", "recommendations"))

    async def track_copy(self, *, prompt_id: uuid.UUID, viewer: User | None) -> EconomyActionRead:
        await self._prompts.track_copy(prompt_id, viewer)

        if viewer is None:
            await self._contributors.refresh_prompt_quality(prompt_id)
            await self._bump_prompt_caches()
            return EconomyActionRead()

        previous_balance = (await self._store.wallet(viewer)).balance
        today_key = datetime.now(timezone.utc).date().isoformat()
        completed: list[str] = []
        completed.extend(
            await self._missions.record_event(
                user=viewer,
                event_type="prompt_copied",
                prompt_id=prompt_id,
            )
        )
        completed.extend(
            await self._missions.record_event(
                user=viewer,
                event_type="streak_activity",
                prompt_id=prompt_id,
                source_event_key=f"streak_activity:{viewer.id}:{today_key}",
                payload={"source": "prompt_copied"},
            )
        )
        await self._contributors.refresh_prompt_quality(prompt_id)
        await self._bump_prompt_caches()
        return await self._store.build_action_feedback(
            viewer,
            previous_balance=previous_balance,
            completed_mission_slugs=list(dict.fromkeys(completed)),
        )

    async def track_apply(self, *, prompt_id: uuid.UUID, viewer: User | None) -> EconomyActionRead:
        if viewer is None:
            return EconomyActionRead()

        previous_balance = (await self._store.wallet(viewer)).balance
        today_key = datetime.now(timezone.utc).date().isoformat()
        completed = await self._missions.record_event(
            user=viewer,
            event_type="prompt_applied",
            prompt_id=prompt_id,
            source_event_key=f"prompt_applied:{viewer.id}:{prompt_id}",
        )
        completed.extend(
            await self._missions.record_event(
                user=viewer,
                event_type="streak_activity",
                prompt_id=prompt_id,
                source_event_key=f"streak_activity:{viewer.id}:{today_key}",
                payload={"source": "prompt_applied"},
            )
        )
        return await self._store.build_action_feedback(
            viewer,
            previous_balance=previous_balance,
            completed_mission_slugs=list(dict.fromkeys(completed)),
        )
