from app.config import Settings
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.config import BILLING_PLAN_COPY
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.billing.service.billing_checkout_mixin import BillingCheckoutMixin
from app.modules.billing.service.billing_plan_mixin import BillingPlanMixin
from app.modules.billing.service.billing_webhook_mixin import BillingWebhookMixin
from app.modules.billing.service.entitlement_service import EntitlementService
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.marketplace.service.marketplace_service import MarketplaceService


class BillingService(BillingPlanMixin, BillingCheckoutMixin, BillingWebhookMixin):
    _PLAN_COPY = BILLING_PLAN_COPY

    def __init__(
        self,
        repo: BillingRepository,
        entitlement_service: EntitlementService,
        user_repo: UserRepository,
        settings: Settings,
        analytics: AnalyticsService | None = None,
        marketplace: MarketplaceService | None = None,
    ) -> None:
        self._repo = repo
        self._entitlements = entitlement_service
        self._users = user_repo
        self._settings = settings
        self._analytics = analytics
        self._marketplace = marketplace
