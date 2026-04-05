from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import case, func, update

from app.infrastructure.db.models import Prompt, PromptModelCompatibility, PromptStats, PromptTag, PromptUseCase


class PromptRepositoryWriteMixin:
    async def create(self, prompt: Prompt) -> Prompt:
        self._session.add(prompt)
        await self._session.flush()
        await self._session.refresh(prompt)
        await self.ensure_prompt_stats(prompt.id)
        return prompt

    async def save(self, prompt: Prompt) -> Prompt:
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt

    async def ensure_prompt_stats(self, prompt_id: uuid.UUID) -> None:
        stmt = self._insert(PromptStats).values(
            prompt_id=prompt_id,
            save_count=0,
            copy_count=0,
            view_count=0,
            quality_score=0,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["prompt_id"])
        await self._session.execute(stmt)

    async def increment_copy_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None:
        await self.ensure_prompt_stats(prompt_id)
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                copy_count=PromptStats.copy_count + amount,
                updated_at=func.now(),
            )
        )

    async def increment_view_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None:
        await self.ensure_prompt_stats(prompt_id)
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                view_count=PromptStats.view_count + amount,
                updated_at=func.now(),
            )
        )

    async def adjust_save_count(self, prompt_id: uuid.UUID, delta: int) -> None:
        await self.ensure_prompt_stats(prompt_id)
        next_value = PromptStats.save_count + delta
        bounded_next_value = (
            func.greatest(next_value, 0)
            if self._is_postgresql()
            else case((next_value < 0, 0), else_=next_value)
        )
        await self._session.execute(
            update(PromptStats)
            .where(PromptStats.prompt_id == prompt_id)
            .values(
                save_count=bounded_next_value,
                updated_at=func.now(),
            )
        )

    async def set_prompt_use_cases(self, prompt_id: uuid.UUID, use_case_ids: Sequence[uuid.UUID]) -> None:
        await self._replace_prompt_links(
            PromptUseCase,
            prompt_id=prompt_id,
            related_key="use_case_id",
            related_ids=use_case_ids,
        )

    async def set_prompt_models(self, prompt_id: uuid.UUID, model_ids: Sequence[uuid.UUID]) -> None:
        await self._replace_prompt_links(
            PromptModelCompatibility,
            prompt_id=prompt_id,
            related_key="model_id",
            related_ids=model_ids,
        )

    async def set_prompt_tags(self, prompt_id: uuid.UUID, tag_ids: Sequence[uuid.UUID]) -> None:
        await self._replace_prompt_links(
            PromptTag,
            prompt_id=prompt_id,
            related_key="tag_id",
            related_ids=tag_ids,
        )
