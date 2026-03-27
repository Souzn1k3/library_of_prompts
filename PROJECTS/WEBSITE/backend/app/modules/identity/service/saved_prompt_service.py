import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.infrastructure.db.models import Prompt, PromptStatus
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository


class SavedPromptRepositoryProtocol(Protocol):
    async def add(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> None: ...

    async def remove(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> bool: ...

    async def list_saved_published_prompts(self, user_id: uuid.UUID) -> Sequence[Prompt]: ...


class PromptRepositoryProtocol(Protocol):
    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None: ...

    async def adjust_save_count(self, prompt_id: uuid.UUID, delta: int) -> None: ...


def _to_list_item(row: Prompt) -> PromptListItem:
    return PromptListItem.model_validate(row)


class SavedPromptService:
    def __init__(
        self,
        saved_repo: SavedPromptRepositoryProtocol,
        prompt_repo: PromptRepositoryProtocol,
    ) -> None:
        self._saved = saved_repo
        self._prompts = prompt_repo

    async def list_saved(self, user_id: uuid.UUID) -> list[PromptListItem]:
        rows = await self._saved.list_saved_published_prompts(user_id)
        return [_to_list_item(r) for r in rows]

    async def save(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> None:
        row = await self._prompts.get_by_id(prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        try:
            await self._saved.add(user_id, prompt_id)
        except IntegrityError as e:
            raise ConflictError(
                "Prompt already saved",
                message_key="errors.prompt_already_saved",
            ) from e
        await self._prompts.adjust_save_count(prompt_id, 1)

    async def unsave(self, user_id: uuid.UUID, prompt_id: uuid.UUID) -> None:
        removed = await self._saved.remove(user_id, prompt_id)
        if not removed:
            raise NotFoundError("saved_prompt", str(prompt_id))
        await self._prompts.adjust_save_count(prompt_id, -1)
