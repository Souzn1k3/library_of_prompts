from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_catalog_service import StoreCatalogService
from app.modules.economy.service.store_purchase_flow_mixin import StorePurchaseFlowMixin
from app.modules.economy.service.store_purchase_helpers_mixin import StorePurchaseHelpersMixin
from app.modules.economy.service.store_reward_service import StoreRewardService
from app.modules.economy.service.wallet_service import WalletService


class StorePurchaseService(StorePurchaseFlowMixin, StorePurchaseHelpersMixin):
    def __init__(
        self,
        store_repo: StoreRepository,
        wallet_repo: WalletRepository,
        wallet_service: WalletService,
        catalog: StoreCatalogService,
        rewards: StoreRewardService,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._store = store_repo
        self._wallet_repo = wallet_repo
        self._wallet = wallet_service
        self._catalog = catalog
        self._rewards = rewards
        self._analytics = analytics
