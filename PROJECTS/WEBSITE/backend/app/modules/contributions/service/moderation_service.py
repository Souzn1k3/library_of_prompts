import uuid
from datetime import datetime, timezone

from app.core.errors import AppError, NotFoundError
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.infrastructure.db.models import ModerationState, PromptStatus, User
from app.modules.catalog.model.prompt import ModerationDecision, ModerationQueueItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.service.contributor_service import ContributorService


class ModerationService:
    def __init__(
        self,
        prompts: PromptRepository,
        contributors: ContributorService,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._prompts = prompts
        self._contributors = contributors
        self._analytics = analytics

    async def queue(self, *, skip: int = 0, limit: int = 50) -> list[ModerationQueueItem]:
        rows = await self._prompts.list_moderation_queue(skip=skip, limit=limit)
        out: list[ModerationQueueItem] = []
        for row in rows:
            contributor = row.author.contributor_profile if row.author and row.author.contributor_profile else None
            out.append(
                ModerationQueueItem(
                    id=row.id,
                    slug=row.slug,
                    title=row.title,
                    summary=row.summary,
                    category_id=row.category_id,
                    author_id=row.author_id,
                    technique=row.technique,
                    contributor_tier=contributor.reputation_tier if contributor else None,
                    contributor_reputation_score=contributor.reputation_score if contributor else None,
                    created_at=row.created_at,
                )
            )
        return out

    async def decide(self, prompt_id: uuid.UUID, decision: ModerationDecision, *, moderator: User) -> None:
        row = await self._prompts.get_by_id(prompt_id)
        if row is None:
            raise NotFoundError("prompt", str(prompt_id))
        if row.moderation_state != ModerationState.pending:
            raise AppError(
                code="not_pending",
                message="This prompt isn't waiting for review.",
                status_code=400,
                message_key="errors.prompt_not_pending",
            )

        if decision.action == "approve":
            row.status = PromptStatus.published
            row.moderation_state = ModerationState.approved
            row.moderation_notes = None
        else:
            if not decision.reason or not decision.reason.strip():
                raise AppError(
                    code="moderation_reason_required",
                    message="Please add a reason before rejecting this prompt.",
                    status_code=400,
                )
            row.moderation_state = ModerationState.rejected
            row.moderation_notes = decision.reason.strip()

        row.auto_approved = False
        row.moderated_by_id = moderator.id
        row.moderated_at = datetime.now(timezone.utc)
        await self._prompts.save(row)
        await self._contributors.refresh_prompt_quality(row.id)
        if row.author_id is not None:
            await self._contributors.recompute_profile_for_user_id(row.author_id)
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.submission_moderated,
                    user_id=row.author_id,
                    metadata={
                        "prompt_id": str(row.id),
                        "decision": decision.action,
                        "moderation_mode": "manual",
                        "moderator_id": str(moderator.id),
                    },
                    context_page="/api/v1/moderation/decision",
                    context_feature="moderation",
                    event_id=f"submission_moderated:manual:{row.id}:{decision.action}",
                )
