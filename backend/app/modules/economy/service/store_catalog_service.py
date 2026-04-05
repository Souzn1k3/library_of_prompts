from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_catalog_feedback_mixin import StoreCatalogFeedbackMixin
from app.modules.economy.service.store_catalog_listing_mixin import StoreCatalogListingMixin
from app.modules.economy.service.store_catalog_offer_mixin import StoreCatalogOfferMixin
from app.modules.economy.service.store_catalog_serialization_mixin import StoreCatalogSerializationMixin
from app.modules.economy.service.store_pricing_service import StorePricingService
from app.modules.economy.service.wallet_service import WalletService


class StoreCatalogService(
    StoreCatalogOfferMixin,
    StoreCatalogSerializationMixin,
    StoreCatalogListingMixin,
    StoreCatalogFeedbackMixin,
):
    def __init__(
        self,
        store_repo: StoreRepository,
        wallet_repo: WalletRepository,
        wallet_service: WalletService,
        pricing: StorePricingService,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._store = store_repo
        self._wallet_repo = wallet_repo
        self._wallet = wallet_service
        self._pricing = pricing
        self._analytics = analytics
