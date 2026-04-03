import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Prompt, PromptStatus, SavedPrompt


class SavedPromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> None:
        self._session.add(SavedPrompt(user_id=user_id, prompt_id=prompt_id))
        await self._session.flush()

    async def remove(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(SavedPrompt).where(
                SavedPrompt.user_id == user_id,
                SavedPrompt.prompt_id == prompt_id,
            )
        )
        return (result.rowcount or 0) > 0

    async def list_saved_published_prompts(self, user_id: uuid.UUID) -> Sequence[Prompt]:
        q = (
            select(Prompt)
            .join(SavedPrompt, SavedPrompt.prompt_id == Prompt.id)
            .where(SavedPrompt.user_id == user_id)
            .where(Prompt.status == PromptStatus.published)
            .order_by(SavedPrompt.created_at.desc())
        )
        result = await self._session.execute(q)
        return result.scalars().all()
