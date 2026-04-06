from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import GuestScenarioRunUsage, ScenarioGameTokenClaim, ScenarioGameTokenEvent


class ScenarioDemoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_guest_run_usage(self, *, guest_id: str, prompt_id: uuid.UUID) -> GuestScenarioRunUsage | None:
        result = await self._session.execute(
            select(GuestScenarioRunUsage).where(
                GuestScenarioRunUsage.guest_id == guest_id,
                GuestScenarioRunUsage.prompt_id == prompt_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_guest_run_usage(self, usage: GuestScenarioRunUsage) -> GuestScenarioRunUsage:
        self._session.add(usage)
        await self._session.flush()
        await self._session.refresh(usage)
        return usage

    async def save_guest_run_usage(self, usage: GuestScenarioRunUsage) -> GuestScenarioRunUsage:
        await self._session.flush()
        await self._session.refresh(usage)
        return usage

    async def sum_guest_runs_for_prompt_ip_since(
        self,
        *,
        prompt_id: uuid.UUID,
        ip_hash: str,
        since: datetime,
    ) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(GuestScenarioRunUsage.run_count), 0)).where(
                GuestScenarioRunUsage.prompt_id == prompt_id,
                GuestScenarioRunUsage.last_ip_hash == ip_hash,
                GuestScenarioRunUsage.last_run_at.is_not(None),
                GuestScenarioRunUsage.last_run_at >= since,
            )
        )
        return int(result.scalar_one() or 0)

    async def get_game_event_by_event_id(self, *, event_id: str) -> ScenarioGameTokenEvent | None:
        result = await self._session.execute(
            select(ScenarioGameTokenEvent).where(ScenarioGameTokenEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def create_game_event(self, event: ScenarioGameTokenEvent) -> ScenarioGameTokenEvent:
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def save_game_event(self, event: ScenarioGameTokenEvent) -> ScenarioGameTokenEvent:
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def get_latest_game_event_for_actor_challenge(
        self,
        *,
        user_id: uuid.UUID | None,
        guest_id: str | None,
        challenge_id: str,
    ) -> ScenarioGameTokenEvent | None:
        if user_id is None and not guest_id:
            return None

        stmt = select(ScenarioGameTokenEvent).where(
            ScenarioGameTokenEvent.challenge_id == challenge_id,
            ScenarioGameTokenEvent.source == "web_demo",
            ScenarioGameTokenEvent.status.in_(["pending", "claimed"]),
        )
        if user_id is not None:
            stmt = stmt.where(ScenarioGameTokenEvent.user_id == user_id)
        else:
            stmt = stmt.where(
                ScenarioGameTokenEvent.user_id.is_(None),
                ScenarioGameTokenEvent.guest_id == guest_id,
            )

        result = await self._session.execute(stmt.order_by(ScenarioGameTokenEvent.occurred_at.desc()).limit(1))
        return result.scalar_one_or_none()

    async def sum_game_tokens_for_actor_since(
        self,
        *,
        user_id: uuid.UUID | None,
        guest_id: str | None,
        since: datetime,
    ) -> int:
        if user_id is None and not guest_id:
            return 0

        stmt = select(func.coalesce(func.sum(ScenarioGameTokenEvent.reward_tokens), 0)).where(
            ScenarioGameTokenEvent.source == "web_demo",
            ScenarioGameTokenEvent.status.in_(["pending", "claimed"]),
            ScenarioGameTokenEvent.occurred_at >= since,
        )
        if user_id is not None:
            stmt = stmt.where(ScenarioGameTokenEvent.user_id == user_id)
        else:
            stmt = stmt.where(
                ScenarioGameTokenEvent.user_id.is_(None),
                ScenarioGameTokenEvent.guest_id == guest_id,
            )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def sum_game_pending_tokens(
        self,
        *,
        user_id: uuid.UUID | None,
        guest_id: str | None,
        include_guest_for_user: bool = False,
    ) -> int:
        if user_id is None and not guest_id:
            return 0

        stmt = select(func.coalesce(func.sum(ScenarioGameTokenEvent.reward_tokens), 0)).where(
            ScenarioGameTokenEvent.source == "web_demo",
            ScenarioGameTokenEvent.status == "pending",
        )
        if user_id is not None and include_guest_for_user and guest_id:
            stmt = stmt.where(
                (ScenarioGameTokenEvent.user_id == user_id)
                | (
                    ScenarioGameTokenEvent.user_id.is_(None)
                    & (ScenarioGameTokenEvent.guest_id == guest_id)
                )
            )
        elif user_id is not None:
            stmt = stmt.where(ScenarioGameTokenEvent.user_id == user_id)
        else:
            stmt = stmt.where(
                ScenarioGameTokenEvent.user_id.is_(None),
                ScenarioGameTokenEvent.guest_id == guest_id,
            )

        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_pending_game_events_for_claim(
        self,
        *,
        user_id: uuid.UUID,
        guest_id: str | None,
    ) -> Sequence[ScenarioGameTokenEvent]:
        actor_filters = [ScenarioGameTokenEvent.user_id == user_id]
        if guest_id:
            actor_filters.append(
                (ScenarioGameTokenEvent.user_id.is_(None))
                & (ScenarioGameTokenEvent.guest_id == guest_id)
            )

        stmt = select(ScenarioGameTokenEvent).where(
            ScenarioGameTokenEvent.source == "web_demo",
            ScenarioGameTokenEvent.status == "pending",
            actor_filters[0] if len(actor_filters) == 1 else actor_filters[0] | actor_filters[1],
        )
        result = await self._session.execute(stmt.order_by(ScenarioGameTokenEvent.occurred_at.asc()))
        return result.scalars().all()

    async def get_game_claim_by_claim_id(self, *, claim_id: str) -> ScenarioGameTokenClaim | None:
        result = await self._session.execute(
            select(ScenarioGameTokenClaim).where(ScenarioGameTokenClaim.claim_id == claim_id)
        )
        return result.scalar_one_or_none()

    async def create_game_claim(self, claim: ScenarioGameTokenClaim) -> ScenarioGameTokenClaim:
        self._session.add(claim)
        await self._session.flush()
        await self._session.refresh(claim)
        return claim

    async def sum_game_claimed_tokens_for_user_since(self, *, user_id: uuid.UUID, since: datetime) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(ScenarioGameTokenClaim.claimed_tokens), 0)).where(
                ScenarioGameTokenClaim.user_id == user_id,
                ScenarioGameTokenClaim.source == "web_demo",
                ScenarioGameTokenClaim.status == "completed",
                ScenarioGameTokenClaim.created_at >= since,
            )
        )
        return int(result.scalar_one() or 0)
