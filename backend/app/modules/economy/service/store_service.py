from app.infrastructure.db.models import StoreItem, User
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.model.store import EconomyActionRead, PurchaseResult, StoreItemRead
from app.modules.economy.model.wallet import WalletRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_catalog_service import StoreCatalogService
from app.modules.economy.service.store_pricing_service import StorePricingService
from app.modules.economy.service.store_purchase_service import StorePurchaseService
from app.modules.economy.service.store_reward_service import StoreRewardService
from app.modules.economy.service.wallet_service import WalletService


class StoreService:
    def __init__(
        self,
        store_repo: StoreRepository,
        wallet_repo: WalletRepository,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._store = store_repo
        self._wallet_repo = wallet_repo
        self._wallet = WalletService(wallet_repo, store_repo, analytics=analytics)
        self._pricing = StorePricingService()
        self._rewards = StoreRewardService()
        self._catalog = StoreCatalogService(
            store_repo,
            wallet_repo,
            self._wallet,
            self._pricing,
            analytics=analytics,
        )
        self._purchase = StorePurchaseService(
            store_repo,
            wallet_repo,
            self._wallet,
            self._catalog,
            self._rewards,
            analytics=analytics,
        )

    async def list_items(self, user: User, *, balance: int | None = None) -> list[StoreItemRead]:
        return await self._catalog.list_items(user, balance=balance)

    async def build_action_feedback(
        self,
        user: User,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead:
        return await self._catalog.build_action_feedback(
            user,
            previous_balance=previous_balance,
            completed_mission_slugs=completed_mission_slugs,
        )

    async def purchase(self, *, user: User, item_slug: str, client_token: str | None = None) -> PurchaseResult:
        return await self._purchase.purchase(user=user, item_slug=item_slug, client_token=client_token)

    async def wallet(self, user: User) -> WalletRead:
        return await self._wallet.get_wallet(user, limit=25)

    async def sync_default_items(self) -> list[StoreItem]:
        return await self._catalog.sync_default_items()


async def sync_default_store_catalog(store_repo: StoreRepository, wallet_repo: WalletRepository) -> list[StoreItem]:
    service = StoreService(store_repo, wallet_repo)
    return await service.sync_default_items()
