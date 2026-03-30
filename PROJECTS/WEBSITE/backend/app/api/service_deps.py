from collections.abc import Callable
from typing import TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.billing.service.billing_service import BillingService
from app.modules.billing.service.entitlement_service import EntitlementService
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.category_service import CategoryService
from app.modules.catalog.service.prompt_service import PromptService
from app.modules.catalog.service.recommendation_service import RecommendationService
from app.modules.contributions.service.submission_service import SubmissionService
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_service import StoreService
from app.modules.economy.service.wallet_service import WalletService
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.education.service.lesson_service import LessonService
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_service import AuthService
from app.modules.identity.service.saved_prompt_service import SavedPromptService
from app.modules.identity.service.user_service import UserService
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.onboarding_service import OnboardingService

ServiceT = TypeVar("ServiceT")


def _db_service(factory: Callable[[AsyncSession], ServiceT]) -> Callable[[AsyncSession], ServiceT]:
    def _dependency(session: AsyncSession = Depends(get_db)) -> ServiceT:
        return factory(session)

    return _dependency


def build_analytics_service(session: AsyncSession) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(session))

get_analytics_service = _db_service(build_analytics_service)


def build_contributor_service(session: AsyncSession) -> ContributorService:
    return ContributorService(ContributorRepository(session), UserRepository(session))

get_contributor_service = _db_service(build_contributor_service)


def build_category_service(session: AsyncSession) -> CategoryService:
    return CategoryService(CategoryRepository(session))

get_category_service = _db_service(build_category_service)


def build_mission_service(session: AsyncSession) -> MissionService:
    return MissionService(
        MissionRepository(session),
        OnboardingRepository(session),
        PromptRepository(session),
        wallet_repo=WalletRepository(session),
        analytics=build_analytics_service(session),
    )

get_mission_service = _db_service(build_mission_service)


def build_wallet_service(session: AsyncSession) -> WalletService:
    return WalletService(WalletRepository(session), StoreRepository(session))

get_wallet_service = _db_service(build_wallet_service)


def build_store_service(session: AsyncSession) -> StoreService:
    wallet_repo = WalletRepository(session)
    return StoreService(StoreRepository(session), wallet_repo)

get_store_service = _db_service(build_store_service)


def build_onboarding_service(session: AsyncSession) -> OnboardingService:
    return OnboardingService(
        OnboardingRepository(session),
        PromptRepository(session),
        LessonRepository(session),
    )

get_onboarding_service = _db_service(build_onboarding_service)


def build_prompt_service(session: AsyncSession) -> PromptService:
    return PromptService(PromptRepository(session), StoreRepository(session))

get_prompt_service = _db_service(build_prompt_service)


def build_recommendation_service(session: AsyncSession) -> RecommendationService:
    return RecommendationService(
        PromptRepository(session),
        SavedPromptRepository(session),
        AnalyticsRepository(session),
        OnboardingRepository(session),
        LessonRepository(session),
        MissionRepository(session),
    )

get_recommendation_service = _db_service(build_recommendation_service)


def build_lesson_service(session: AsyncSession) -> LessonService:
    return LessonService(LessonRepository(session))

get_lesson_service = _db_service(build_lesson_service)


def build_submission_service(session: AsyncSession) -> SubmissionService:
    return SubmissionService(
        PromptRepository(session),
        CategoryRepository(session),
        build_contributor_service(session),
        analytics=build_analytics_service(session),
    )

get_submission_service = _db_service(build_submission_service)


def build_auth_service(session: AsyncSession) -> AuthService:
    return AuthService(
        UserRepository(session),
        RefreshTokenRepository(session),
        get_settings(),
        analytics=build_analytics_service(session),
    )

get_auth_service = _db_service(build_auth_service)


def build_user_service(session: AsyncSession) -> UserService:
    return UserService(UserRepository(session))

get_user_service = _db_service(build_user_service)


def build_saved_prompt_service(session: AsyncSession) -> SavedPromptService:
    return SavedPromptService(
        SavedPromptRepository(session),
        PromptRepository(session),
    )

get_saved_prompt_service = _db_service(build_saved_prompt_service)


def build_billing_service(session: AsyncSession) -> BillingService:
    billing_repo = BillingRepository(session)
    user_repo = UserRepository(session)
    entitlements = EntitlementService(billing_repo, user_repo)
    return BillingService(
        billing_repo,
        entitlements,
        user_repo,
        get_settings(),
        analytics=build_analytics_service(session),
    )

get_billing_service = _db_service(build_billing_service)
