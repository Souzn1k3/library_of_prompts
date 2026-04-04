from functools import cached_property

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
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


def build_analytics_service(session: AsyncSession) -> AnalyticsService:
    return _container(session).analytics_service


def build_contributor_service(session: AsyncSession) -> ContributorService:
    return _container(session).contributor_service


def build_category_service(session: AsyncSession) -> CategoryService:
    return _container(session).category_service


def build_mission_service(session: AsyncSession) -> MissionService:
    return _container(session).mission_service


def build_wallet_service(session: AsyncSession) -> WalletService:
    return _container(session).wallet_service


def build_store_service(session: AsyncSession) -> StoreService:
    return _container(session).store_service


def build_economy_insights_service(session: AsyncSession) -> EconomyInsightsService:
    return _container(session).economy_insights_service


def build_economy_kpi_service(session: AsyncSession) -> EconomyKpiService:
    return _container(session).economy_kpi_service


def build_marketplace_service(session: AsyncSession) -> MarketplaceService:
    return _container(session).marketplace_service


def build_onboarding_service(session: AsyncSession) -> OnboardingService:
    return _container(session).onboarding_service


def build_prompt_service(session: AsyncSession) -> PromptService:
    return _container(session).prompt_service


def build_recommendation_service(session: AsyncSession) -> RecommendationService:
    return _container(session).recommendation_service


def build_lesson_service(session: AsyncSession) -> LessonService:
    return _container(session).lesson_service


def build_learning_service(session: AsyncSession) -> LearningService:
    return _container(session).learning_service


def build_submission_service(session: AsyncSession) -> SubmissionService:
    return _container(session).submission_service


def build_moderation_service(session: AsyncSession) -> ModerationService:
    return _container(session).moderation_service


def build_auth_service(session: AsyncSession) -> AuthService:
    return _container(session).auth_service


def build_user_service(session: AsyncSession) -> UserService:
    return _container(session).user_service


def build_saved_prompt_service(session: AsyncSession) -> SavedPromptService:
    return _container(session).saved_prompt_service


def build_billing_service(session: AsyncSession) -> BillingService:
    return _container(session).billing_service


def get_analytics_service(container: ServiceContainer = Depends(get_service_container)) -> AnalyticsService:
    return container.analytics_service


def get_contributor_service(container: ServiceContainer = Depends(get_service_container)) -> ContributorService:
    return container.contributor_service


def get_category_service(container: ServiceContainer = Depends(get_service_container)) -> CategoryService:
    return container.category_service


def get_mission_service(container: ServiceContainer = Depends(get_service_container)) -> MissionService:
    return container.mission_service


def get_wallet_service(container: ServiceContainer = Depends(get_service_container)) -> WalletService:
    return container.wallet_service


def get_store_service(container: ServiceContainer = Depends(get_service_container)) -> StoreService:
    return container.store_service


def get_economy_insights_service(
    container: ServiceContainer = Depends(get_service_container),
) -> EconomyInsightsService:
    return container.economy_insights_service


def get_economy_kpi_service(container: ServiceContainer = Depends(get_service_container)) -> EconomyKpiService:
    return container.economy_kpi_service


def get_marketplace_service(container: ServiceContainer = Depends(get_service_container)) -> MarketplaceService:
    return container.marketplace_service


def get_onboarding_service(container: ServiceContainer = Depends(get_service_container)) -> OnboardingService:
    return container.onboarding_service


def get_prompt_service(container: ServiceContainer = Depends(get_service_container)) -> PromptService:
    return container.prompt_service


def get_recommendation_service(
    container: ServiceContainer = Depends(get_service_container),
) -> RecommendationService:
    return container.recommendation_service


def get_lesson_service(container: ServiceContainer = Depends(get_service_container)) -> LessonService:
    return container.lesson_service


def get_learning_service(container: ServiceContainer = Depends(get_service_container)) -> LearningService:
    return container.learning_service


def get_submission_service(container: ServiceContainer = Depends(get_service_container)) -> SubmissionService:
    return container.submission_service


def get_moderation_service(container: ServiceContainer = Depends(get_service_container)) -> ModerationService:
    return container.moderation_service


def get_auth_service(container: ServiceContainer = Depends(get_service_container)) -> AuthService:
    return container.auth_service


def get_user_service(container: ServiceContainer = Depends(get_service_container)) -> UserService:
    return container.user_service


def get_saved_prompt_service(container: ServiceContainer = Depends(get_service_container)) -> SavedPromptService:
    return container.saved_prompt_service


def get_billing_service(container: ServiceContainer = Depends(get_service_container)) -> BillingService:
    return container.billing_service
