from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import UserScenarioWorkspace


class ScenarioWorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_workspace_entry(self, *, user_id: uuid.UUID, prompt_id: uuid.UUID) -> UserScenarioWorkspace | None:
        result = await self._session.execute(
            select(UserScenarioWorkspace).where(
                UserScenarioWorkspace.user_id == user_id,
                UserScenarioWorkspace.prompt_id == prompt_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_workspace_entries(self, *, user_id: uuid.UUID) -> Sequence[UserScenarioWorkspace]:
        result = await self._session.execute(
            select(UserScenarioWorkspace)
            .where(UserScenarioWorkspace.user_id == user_id)
            .order_by(UserScenarioWorkspace.last_used_at.desc())
        )
        return result.scalars().all()

    async def create_workspace_entry(self, entry: UserScenarioWorkspace) -> UserScenarioWorkspace:
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def save_workspace_entry(self, entry: UserScenarioWorkspace) -> UserScenarioWorkspace:
        await self._session.flush()
        await self._session.refresh(entry)
        return entry
