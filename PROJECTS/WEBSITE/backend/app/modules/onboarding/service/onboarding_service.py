import uuid
from datetime import datetime, timezone

from app.core.errors import AppError, NotFoundError
from app.core.tiers import can_view_lesson
from app.infrastructure.db.models import OnboardingProfile, PromptStatus, User
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.education.model.lesson import LessonListItem
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.onboarding.model.onboarding import (
    FirstWinCompleteRequest,
    OnboardingProfileRead,
    OnboardingProfileUpdate,
    OnboardingStarterAction,
    OnboardingStarterLesson,
    OnboardingStarterPack,
    OnboardingStarterPrompt,
)
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.persona_hints import build_persona_hint_query


def _to_profile_read(profile: OnboardingProfile | None) -> OnboardingProfileRead:
    if profile is None:
        return OnboardingProfileRead(
            role=None,
            goal=None,
            ai_context=None,
            completed_at=None,
            skipped_at=None,
            first_win_prompt_id=None,
            first_win_completed_at=None,
            is_completed=False,
            is_skipped=False,
            needs_onboarding=True,
        )
    is_completed = profile.completed_at is not None
    is_skipped = profile.skipped_at is not None
    return OnboardingProfileRead(
        role=profile.role,
        goal=profile.goal,
        ai_context=profile.ai_context,
        completed_at=profile.completed_at,
        skipped_at=profile.skipped_at,
        first_win_prompt_id=profile.first_win_prompt_id,
        first_win_completed_at=profile.first_win_completed_at,
        is_completed=is_completed,
        is_skipped=is_skipped,
        needs_onboarding=not is_completed and not is_skipped,
    )


def _starter_prompt_from_list_item(row: PromptListItem) -> OnboardingStarterPrompt:
    return OnboardingStarterPrompt(
        id=row.id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        technique=row.technique.value,
        category_id=row.category_id,
    )


class OnboardingService:
    def __init__(
        self,
        repo: OnboardingRepository,
        prompt_repo: PromptRepository,
        lesson_repo: LessonRepository,
    ) -> None:
        self._repo = repo
        self._prompts = prompt_repo
        self._lessons = lesson_repo

    async def get_profile(self, user: User) -> OnboardingProfileRead:
        profile = await self._repo.get_profile(user.id)
        return _to_profile_read(profile)

    async def upsert_profile(self, user: User, body: OnboardingProfileUpdate) -> OnboardingProfileRead:
        now = datetime.now(timezone.utc)
        profile = await self._repo.get_profile(user.id)
        if profile is None:
            profile = OnboardingProfile(user_id=user.id)
            await self._repo.create_profile(profile)

        profile.role = body.role
        profile.goal = body.goal
        profile.ai_context = body.ai_context.strip().lower()
        if profile.completed_at is None:
            profile.completed_at = now
        profile.skipped_at = None
        await self._repo.save_profile(profile)

        await self._repo.add_event(
            user_id=user.id,
            event_name="onboarding_completed",
            payload={
                "role": profile.role.value if profile.role else None,
                "goal": profile.goal.value if profile.goal else None,
                "ai_context": profile.ai_context,
            },
        )
        return _to_profile_read(profile)

    async def skip(self, user: User) -> OnboardingProfileRead:
        now = datetime.now(timezone.utc)
        profile = await self._repo.get_profile(user.id)
        if profile is None:
            profile = OnboardingProfile(user_id=user.id)
            await self._repo.create_profile(profile)
        profile.skipped_at = now
        await self._repo.save_profile(profile)
        await self._repo.add_event(user_id=user.id, event_name="onboarding_skipped", payload=None)
        return _to_profile_read(profile)

    async def starter_pack(self, user: User) -> OnboardingStarterPack:
        profile = await self._repo.get_profile(user.id)
        role = profile.role.value if profile and profile.role else "other"
        goal = profile.goal.value if profile and profile.goal else "learning"
        context = profile.ai_context if profile and profile.ai_context else "chatgpt"
        q = build_persona_hint_query(
            role=role,
            goal=goal,
            context=context,
            extra_hints=["explain"] if goal == "learning" else None,
        )

        prompt_rows = await self._prompts.list_published(
            skip=0,
            limit=25,
            q=q,
            restrict_to_unrestricted_categories=True,
            only_free=True,
        )
        if not prompt_rows:
            prompt_rows = await self._prompts.list_published(
                skip=0,
                limit=25,
                restrict_to_unrestricted_categories=True,
                only_free=True,
            )

        starter_items = [PromptListItem.model_validate(row) for row in prompt_rows][:5]
        if len(starter_items) < 3:
            additional_rows = await self._prompts.list_published(
                skip=0,
                limit=50,
                restrict_to_unrestricted_categories=True,
                only_free=True,
            )
            existing_ids = {item.id for item in starter_items}
            for row in additional_rows:
                li = PromptListItem.model_validate(row)
                if li.id in existing_ids:
                    continue
                starter_items.append(li)
                existing_ids.add(li.id)
                if len(starter_items) >= 5:
                    break

            if len(starter_items) < 3:
                broader_rows = await self._prompts.list_published(
                    skip=0,
                    limit=50,
                    restrict_to_unrestricted_categories=True,
                    only_free=False,
                )
                for row in broader_rows:
                    li = PromptListItem.model_validate(row)
                    if li.id in existing_ids:
                        continue
                    starter_items.append(li)
                    existing_ids.add(li.id)
                    if len(starter_items) >= 5:
                        break

        prompts = [_starter_prompt_from_list_item(item) for item in starter_items[:5]]

        lessons = await self._lessons.list_all()
        lesson_item: OnboardingStarterLesson | None = None
        if lessons:
            selected = None
            for lesson in lessons:
                if can_view_lesson(user, lesson.min_tier):
                    selected = lesson
                    break
            if selected is None:
                selected = lessons[0]
            base = LessonListItem.model_validate(selected)
            lesson_item = OnboardingStarterLesson(
                id=base.id,
                slug=base.slug,
                title=base.title,
                min_tier=base.min_tier,
                locked=not can_view_lesson(user, base.min_tier),
            )

        action: OnboardingStarterAction | None = None
        if prompts:
            first_prompt = await self._prompts.get_by_id(prompts[0].id)
            if first_prompt is not None and first_prompt.status == PromptStatus.published and not first_prompt.is_premium:
                action = OnboardingStarterAction(
                    prompt_id=first_prompt.id,
                    prompt_slug=first_prompt.slug,
                    prompt_title=first_prompt.title,
                    prompt_body=first_prompt.body,
                    instruction="Copy this prompt, run it in your preferred AI tool, and compare results.",
                )

        return OnboardingStarterPack(prompts=prompts, lesson=lesson_item, action=action)

    async def complete_first_win(self, user: User, body: FirstWinCompleteRequest) -> OnboardingProfileRead:
        profile = await self._repo.get_profile(user.id)
        if profile is None:
            raise AppError(
                code="onboarding_profile_not_found",
                message="Please complete onboarding first.",
                status_code=400,
                message_key="errors.onboarding_profile_not_found",
            )

        row = await self._prompts.get_by_id(body.prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(body.prompt_id))

        now = datetime.now(timezone.utc)
        profile.first_win_prompt_id = body.prompt_id
        profile.first_win_completed_at = now
        if profile.completed_at is None:
            profile.completed_at = now
        await self._repo.save_profile(profile)

        await self._repo.add_event(
            user_id=user.id,
            event_name="onboarding_first_win_completed",
            payload={"prompt_id": str(body.prompt_id), "action": body.action},
        )
        return _to_profile_read(profile)
