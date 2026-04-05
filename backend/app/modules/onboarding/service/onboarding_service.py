from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.onboarding_profile_mixin import OnboardingProfileMixin
from app.modules.onboarding.service.onboarding_starter_pack_mixin import OnboardingStarterPackMixin


class OnboardingService(OnboardingProfileMixin, OnboardingStarterPackMixin):
    def __init__(
        self,
        repo: OnboardingRepository,
        prompt_repo: PromptRepository,
        lesson_repo: LessonRepository,
    ) -> None:
        self._repo = repo
        self._prompts = prompt_repo
        self._lessons = lesson_repo
