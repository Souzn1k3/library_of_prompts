import uuid

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.infrastructure.db.models import ModerationState, Prompt, PromptStatus
from app.modules.catalog.model.prompt import PromptSubmissionResult, PromptSubmit
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository


class SubmissionService:
    def __init__(
        self,
        prompts: PromptRepository,
        categories: CategoryRepository,
    ) -> None:
        self._prompts = prompts
        self._categories = categories

    async def submit(self, user_id: uuid.UUID, data: PromptSubmit) -> PromptSubmissionResult:
        cat = await self._categories.get_by_id(data.category_id)
        if cat is None:
            raise NotFoundError("category", str(data.category_id))

        prompt = Prompt(
            slug=data.slug,
            title=data.title.strip(),
            body=data.body,
            summary=data.summary.strip() if data.summary else None,
            status=PromptStatus.draft,
            technique=data.technique,
            moderation_state=ModerationState.pending,
            category_id=data.category_id,
            author_id=user_id,
            is_premium=False,
        )
        try:
            created = await self._prompts.create(prompt)
        except IntegrityError as e:
            raise ConflictError("Slug already taken") from e
        return PromptSubmissionResult(
            id=created.id,
            slug=created.slug,
            status=created.status,
            moderation_state=created.moderation_state,
        )
