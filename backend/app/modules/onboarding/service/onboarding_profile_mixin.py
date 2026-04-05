from datetime import datetime, timezone

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import OnboardingProfile, PromptStatus, User
from app.modules.onboarding.model.onboarding import (
    FirstWinCompleteRequest,
    OnboardingProfileRead,
    OnboardingProfileUpdate,
)
from app.modules.onboarding.service.onboarding_support import to_profile_read


class OnboardingProfileMixin:
    async def _get_or_create_profile(self, user: User) -> OnboardingProfile:
        profile = await self._repo.get_profile(user.id)
        if profile is None:
            profile = OnboardingProfile(user_id=user.id)
            await self._repo.create_profile(profile)
        return profile

    async def get_profile(self, user: User) -> OnboardingProfileRead:
        profile = await self._repo.get_profile(user.id)
        return to_profile_read(profile)

    async def upsert_profile(self, user: User, body: OnboardingProfileUpdate) -> OnboardingProfileRead:
        now = datetime.now(timezone.utc)
        profile = await self._get_or_create_profile(user)

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
        return to_profile_read(profile)

    async def skip(self, user: User) -> OnboardingProfileRead:
        now = datetime.now(timezone.utc)
        profile = await self._get_or_create_profile(user)
        profile.skipped_at = now
        await self._repo.save_profile(profile)
        await self._repo.add_event(user_id=user.id, event_name="onboarding_skipped", payload=None)
        return to_profile_read(profile)

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
        return to_profile_read(profile)
