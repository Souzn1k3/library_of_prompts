from app.infrastructure.db.models import OnboardingProfile
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.onboarding.model.onboarding import OnboardingProfileRead, OnboardingStarterPrompt


def to_profile_read(profile: OnboardingProfile | None) -> OnboardingProfileRead:
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


def starter_prompt_from_list_item(row: PromptListItem) -> OnboardingStarterPrompt:
    return OnboardingStarterPrompt(
        id=row.id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        technique=row.technique.value,
        category_id=row.category_id,
    )
