from functools import cached_property

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.cache import get_cache
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.billing.service.billing_service import BillingService
from app.modules.billing.service.entitlement_service import EntitlementService
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.category_service import CategoryService
from app.modules.catalog.service.prompt_engagement_service import PromptEngagementService
from app.modules.catalog.service.prompt_service import PromptService
from app.modules.catalog.service.recommendation_service import RecommendationService
from app.modules.contributions.service.moderation_service import ModerationService
from app.modules.contributions.service.submission_service import SubmissionService
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.economy.repository.insights_repository import EconomyInsightsRepository
from app.modules.economy.repository.kpi_repository import EconomyKpiRepository
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.insights_service import EconomyInsightsService
from app.modules.economy.service.kpi_service import EconomyKpiService
from app.modules.economy.service.store_service import StoreService
from app.modules.economy.service.wallet_service import WalletService
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.education.service.lesson_service import LessonService
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_service import AuthService
from app.modules.identity.service.display_name_policy import DisplayNamePolicy
from app.modules.identity.service.saved_prompt_service import SavedPromptService
from app.modules.identity.service.user_service import UserService
from app.modules.learning.repository.learning_repository import LearningRepository
from app.modules.learning.service.learning_service import LearningService
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.marketplace_service import MarketplaceService
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.onboarding_service import OnboardingService


class ServiceContainer:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @cached_property
    def settings(self) -> Settings:
        return get_settings()

    @cached_property
    def analytics_repository(self) -> AnalyticsRepository:
        return AnalyticsRepository(self._session)

    @cached_property
    def billing_repository(self) -> BillingRepository:
        return BillingRepository(self._session)

    @cached_property
    def category_repository(self) -> CategoryRepository:
        return CategoryRepository(self._session)

    @cached_property
    def contributor_repository(self) -> ContributorRepository:
        return ContributorRepository(self._session)

    @cached_property
    def marketplace_repository(self) -> MarketplaceRepository:
        return MarketplaceRepository(self._session)

    @cached_property
    def mission_repository(self) -> MissionRepository:
        return MissionRepository(self._session)

    @cached_property
    def onboarding_repository(self) -> OnboardingRepository:
        return OnboardingRepository(self._session)

    @cached_property
    def prompt_repository(self) -> PromptRepository:
        return PromptRepository(self._session)

    @cached_property
    def refresh_token_repository(self) -> RefreshTokenRepository:
        return RefreshTokenRepository(self._session)

    @cached_property
    def saved_prompt_repository(self) -> SavedPromptRepository:
        return SavedPromptRepository(self._session)

    @cached_property
    def store_repository(self) -> StoreRepository:
        return StoreRepository(self._session)

    @cached_property
    def user_repository(self) -> UserRepository:
        return UserRepository(self._session)

    @cached_property
    def wallet_repository(self) -> WalletRepository:
        return WalletRepository(self._session)

    @cached_property
    def learning_repository(self) -> LearningRepository:
        return LearningRepository(self._session)

    @cached_property
    def lesson_repository(self) -> LessonRepository:
        return LessonRepository(self._session)

    @cached_property
    def economy_insights_repository(self) -> EconomyInsightsRepository:
        return EconomyInsightsRepository(self._session)

    @cached_property
    def economy_kpi_repository(self) -> EconomyKpiRepository:
        return EconomyKpiRepository(self._session)

    @cached_property
    def display_name_policy(self) -> DisplayNamePolicy:
        return DisplayNamePolicy()

    @cached_property
    def analytics_service(self) -> AnalyticsService:
        return AnalyticsService(self.analytics_repository)

    @cached_property
    def marketplace_service(self) -> MarketplaceService:
        return MarketplaceService(
            self.marketplace_repository,
            self.billing_repository,
            self.wallet_repository,
            self.store_repository,
            self.settings,
        )

    @cached_property
    def contributor_service(self) -> ContributorService:
        return ContributorService(
            self.contributor_repository,
            self.user_repository,
            marketplace=self.marketplace_service,
        )

    @cached_property
    def category_service(self) -> CategoryService:
        return CategoryService(self.category_repository)

    @cached_property
    def mission_service(self) -> MissionService:
        return MissionService(
            self.mission_repository,
            self.onboarding_repository,
            self.prompt_repository,
            wallet_repo=self.wallet_repository,
            analytics=self.analytics_service,
        )

    @cached_property
    def wallet_service(self) -> WalletService:
        return WalletService(
            self.wallet_repository,
            self.store_repository,
            analytics=self.analytics_service,
        )

    @cached_property
    def store_service(self) -> StoreService:
        return StoreService(
            self.store_repository,
            self.wallet_repository,
            analytics=self.analytics_service,
        )

    @cached_property
    def economy_insights_service(self) -> EconomyInsightsService:
        return EconomyInsightsService(self.economy_insights_repository)

    @cached_property
    def economy_kpi_service(self) -> EconomyKpiService:
        return EconomyKpiService(self.economy_kpi_repository)

    @cached_property
    def onboarding_service(self) -> OnboardingService:
        return OnboardingService(
            self.onboarding_repository,
            self.prompt_repository,
            self.lesson_repository,
        )

    @cached_property
    def prompt_service(self) -> PromptService:
        return PromptService(
            self.prompt_repository,
            self.store_repository,
            marketplace=self.marketplace_service,
        )

    @cached_property
    def prompt_engagement_service(self) -> PromptEngagementService:
        return PromptEngagementService(
            prompts=self.prompt_service,
            missions=self.mission_service,
            contributors=self.contributor_service,
            store=self.store_service,
            cache=get_cache(),
        )

    @cached_property
    def recommendation_service(self) -> RecommendationService:
        return RecommendationService(
            self.prompt_repository,
            self.saved_prompt_repository,
            self.analytics_repository,
            self.onboarding_repository,
            self.lesson_repository,
            self.mission_repository,
        )

    @cached_property
    def lesson_service(self) -> LessonService:
        return LessonService(self.lesson_repository)

    @cached_property
    def learning_service(self) -> LearningService:
        return LearningService(
            self.learning_repository,
            self.wallet_repository,
        )

    @cached_property
    def submission_service(self) -> SubmissionService:
        return SubmissionService(
            self.prompt_repository,
            self.category_repository,
            self.contributor_service,
            marketplace=self.marketplace_service,
            analytics=self.analytics_service,
        )

    @cached_property
    def moderation_service(self) -> ModerationService:
        return ModerationService(
            self.prompt_repository,
            self.contributor_service,
            analytics=self.analytics_service,
        )

    @cached_property
    def auth_service(self) -> AuthService:
        return AuthService(
            self.user_repository,
            self.refresh_token_repository,
            self.settings,
            analytics=self.analytics_service,
            display_names=self.display_name_policy,
        )

    @cached_property
    def user_service(self) -> UserService:
        return UserService(
            self.user_repository,
            contributors=self.contributor_service,
            marketplace=self.marketplace_service,
            display_names=self.display_name_policy,
        )

    @cached_property
    def saved_prompt_service(self) -> SavedPromptService:
        return SavedPromptService(
            self.saved_prompt_repository,
            self.prompt_repository,
        )

    @cached_property
    def billing_service(self) -> BillingService:
        entitlements = EntitlementService(self.billing_repository, self.user_repository)
        return BillingService(
            self.billing_repository,
            entitlements,
            self.user_repository,
            self.settings,
            analytics=self.analytics_service,
            marketplace=self.marketplace_service,
        )


def _container(session: AsyncSession) -> ServiceContainer:
    return ServiceContainer(session)


def get_service_container(session: AsyncSession = Depends(get_db)) -> ServiceContainer:
    return _container(session)


__all__ = ("ServiceContainer", "_container", "get_service_container")
