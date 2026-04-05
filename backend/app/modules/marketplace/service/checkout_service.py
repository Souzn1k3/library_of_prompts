from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.config import Settings
from app.infrastructure.db.models import MarketplacePayout, PromptPurchase
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.model.marketplace import PromptPurchaseRead
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.access_service import MarketplaceAccessService
from app.modules.marketplace.service.marketplace_checkout_helper_mixin import MarketplaceCheckoutHelperMixin
from app.modules.marketplace.service.marketplace_checkout_purchase_mixin import MarketplaceCheckoutPurchaseMixin
from app.modules.marketplace.service.marketplace_checkout_refund_mixin import MarketplaceCheckoutRefundMixin


class MarketplaceCheckoutService(
    MarketplaceCheckoutRefundMixin,
    MarketplaceCheckoutPurchaseMixin,
    MarketplaceCheckoutHelperMixin,
):
    def __init__(
        self,
        repo: MarketplaceRepository,
        wallet_repo: WalletRepository,
        store_repo: StoreRepository,
        settings: Settings,
        access_service: MarketplaceAccessService,
        purchase_to_read: Callable[[PromptPurchase, bool | None], PromptPurchaseRead],
        sync_reserved_payout: Callable[[MarketplacePayout], Awaitable[MarketplacePayout]],
    ) -> None:
        self._repo = repo
        self._wallet = wallet_repo
        self._store = store_repo
        self._settings = settings
        self._access = access_service
        self._purchase_to_read = purchase_to_read
        self._sync_reserved_payout = sync_reserved_payout
