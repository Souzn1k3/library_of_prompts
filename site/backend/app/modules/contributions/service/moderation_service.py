import uuid

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import ModerationState, PromptStatus
from app.modules.catalog.model.prompt import ModerationDecision, ModerationQueueItem
from app.modules.catalog.repository.prompt_repository import PromptRepository


class ModerationService:
    def __init__(self, prompts: PromptRepository) -> None:
        self._prompts = prompts

    async def queue(self, *, skip: int = 0, limit: int = 50) -> list[ModerationQueueItem]:
        rows = await self._prompts.list_moderation_queue(skip=skip, limit=limit)
        return [ModerationQueueItem.model_validate(r) for r in rows]

    async def decide(self, prompt_id: uuid.UUID, decision: ModerationDecision) -> None:
        row = await self._prompts.get_by_id(prompt_id)
        if row is None:
            raise NotFoundError("prompt", str(prompt_id))
        if row.moderation_state != ModerationState.pending:
            raise AppError(
                code="not_pending",
                message="Prompt is not awaiting moderation",
                status_code=400,
            )

        if decision.action == "approve":
            row.status = PromptStatus.published
            row.moderation_state = ModerationState.approved
            row.moderation_notes = None
        else:
            row.moderation_state = ModerationState.rejected
            row.moderation_notes = decision.reason
        await self._prompts.save(row)
