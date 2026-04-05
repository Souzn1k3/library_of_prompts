from app.core.tiers import can_view_lesson
from app.infrastructure.db.models import PromptStatus, User
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.education.model.lesson import LessonListItem
from app.modules.onboarding.model.onboarding import (
    OnboardingStarterAction,
    OnboardingStarterLesson,
    OnboardingStarterPack,
)
from app.modules.onboarding.service.onboarding_support import starter_prompt_from_list_item
from app.modules.onboarding.service.persona_hints import build_persona_hint_query


class OnboardingStarterPackMixin:
    async def _collect_starter_prompt_items(self, *, q: str) -> list[PromptListItem]:
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
        if len(starter_items) >= 3:
            return starter_items[:5]

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
                return starter_items[:5]

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
        return starter_items[:5]

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

        starter_items = await self._collect_starter_prompt_items(q=q)
        prompts = [starter_prompt_from_list_item(item) for item in starter_items]

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
