from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.infrastructure.db.models import Prompt
from app.modules.catalog.repository.prompt_repository_projection_mixin import PromptRepositoryProjectionMixin
from app.modules.catalog.repository.prompt_repository_query_mixin import PromptRepositoryQueryMixin


class PromptRepositoryBaseMixin(
    PromptRepositoryProjectionMixin,
    PromptRepositoryQueryMixin,
):
    def _is_postgresql(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "postgresql")

    def _insert(self, model: Any):
        return pg_insert(model) if self._is_postgresql() else sqlite_insert(model)

    async def _get_prompt(self, *conditions: Any) -> Prompt | None:
        stmt = select(Prompt).options(*self._prompt_detail_load_options()).where(*conditions)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _replace_prompt_links(
        self,
        model: Any,
        *,
        prompt_id: uuid.UUID,
        related_key: str,
        related_ids: Sequence[uuid.UUID],
    ) -> None:
        await self._session.execute(delete(model).where(model.prompt_id == prompt_id))
        if not related_ids:
            return
        rows = [{"prompt_id": prompt_id, related_key: related_id} for related_id in related_ids]
        await self._session.execute(self._insert(model).values(rows))
