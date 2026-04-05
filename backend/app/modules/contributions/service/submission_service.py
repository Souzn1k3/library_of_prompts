from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.infrastructure.db.models import ModerationState, Prompt, PromptStatus, User
from app.modules.catalog.model.prompt import PromptSubmissionResult, PromptSubmit
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.marketplace.service.marketplace_service import MarketplaceService


class SubmissionService:
    def __init__(
        self,
        prompts: PromptRepository,
        categories: CategoryRepository,
        contributors: ContributorService,
        marketplace: MarketplaceService | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._prompts = prompts
        self._categories = categories
        self._contributors = contributors
        self._marketplace = marketplace
        self._analytics = analytics

    async def submit(self, user: User, data: PromptSubmit) -> PromptSubmissionResult:
        await self._contributors.apply_submission_guardrails(
            user,
            title=data.title,
            body=data.body,
            summary=data.summary,
        )
        cat = await self._categories.get_by_id(data.category_id)
        if cat is None:
            raise NotFoundError("category", str(data.category_id))

        trusted_auto_approve = await self._contributors.should_auto_approve(user)
        passes_auto_quality = (
            len(data.body.strip()) >= 180
            and bool(data.summary and data.summary.strip())
            and len(data.tags) >= 1
        )
        auto_approve = trusted_auto_approve and passes_auto_quality
        now = datetime.now(timezone.utc)

        prompt = Prompt(
            slug=data.slug,
            title=data.title.strip(),
            body=data.body,
            summary=data.summary.strip() if data.summary else None,
            status=PromptStatus.published if auto_approve else PromptStatus.draft,
            technique=data.technique,
            difficulty=data.difficulty,
            output_type=data.output_type,
            moderation_state=ModerationState.approved if auto_approve else ModerationState.pending,
            category_id=data.category_id,
            author_id=user.id,
            is_premium=False,
            auto_approved=auto_approve,
            moderated_at=now if auto_approve else None,
            moderated_by_id=None,
            moderation_notes="Auto-approved for trusted contributor" if auto_approve else None,
        )
        try:
            created = await self._prompts.create(prompt)
        except IntegrityError as e:
            raise ConflictError(
                "Slug already taken",
                message_key="errors.slug_already_taken",
            ) from e
        if self._marketplace is not None:
            await self._marketplace.upsert_prompt_price(created, data.price_rub)

        if data.use_cases:
            use_case_rows = await self._prompts.get_use_cases_by_slugs(data.use_cases)
            found = {row.slug for row in use_case_rows}
            missing = [slug for slug in data.use_cases if slug not in found]
            if missing:
                raise AppError(
                    code="invalid_use_case",
                    message="Some selected use cases are no longer available.",
                    status_code=400,
                    message_key="errors.invalid_use_case",
                    details={"missing": missing},
                )
            await self._prompts.set_prompt_use_cases(created.id, [row.id for row in use_case_rows])

        if data.model_compatibility:
            model_rows = await self._prompts.get_model_compatibility_by_slugs(data.model_compatibility)
            found = {row.slug for row in model_rows}
            missing = [slug for slug in data.model_compatibility if slug not in found]
            if missing:
                raise AppError(
                    code="invalid_model_compatibility",
                    message="Some selected models are no longer available.",
                    status_code=400,
                    message_key="errors.invalid_model_compatibility",
                    details={"missing": missing},
                )
            await self._prompts.set_prompt_models(created.id, [row.id for row in model_rows])

        if data.tags:
            tag_rows = await self._prompts.get_tags_by_slugs(data.tags)
            found = {row.slug for row in tag_rows}
            missing = [slug for slug in data.tags if slug not in found]
            if missing:
                raise AppError(
                    code="invalid_tag",
                    message="Some selected tags are no longer available.",
                    status_code=400,
                    message_key="errors.invalid_tag",
                    details={"missing": missing},
                )
            await self._prompts.set_prompt_tags(created.id, [row.id for row in tag_rows])

        await self._contributors.refresh_prompt_quality(created.id)
        await self._contributors.recompute_profile_for_user(user)
        if self._analytics is not None:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.submission_created,
                user_id=user.id,
                metadata={
                    "prompt_id": str(created.id),
                    "prompt_slug": created.slug,
                    "moderation_state": created.moderation_state.value,
                    "auto_approved": created.auto_approved,
                },
                context_page="/api/v1/contributions/submit",
                context_feature="contributor_submission",
                event_id=f"submission_created:{created.id}",
            )
            if created.moderation_state == ModerationState.approved:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.submission_moderated,
                    user_id=user.id,
                    metadata={
                        "prompt_id": str(created.id),
                        "decision": "approved",
                        "moderation_mode": "auto",
                    },
                    context_page="/api/v1/contributions/submit",
                    context_feature="contributor_submission",
                    event_id=f"submission_moderated:auto:{created.id}",
                )

        return PromptSubmissionResult(
            id=created.id,
            slug=created.slug,
            status=created.status,
            moderation_state=created.moderation_state,
            auto_approved=created.auto_approved,
        )
