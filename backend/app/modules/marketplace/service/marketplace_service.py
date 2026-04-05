from __future__ import annotations

from app.config import Settings
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.access_service import MarketplaceAccessService
from app.modules.marketplace.service.checkout_service import MarketplaceCheckoutService
from app.modules.marketplace.service.marketplace_projection_mixin import MarketplaceProjectionMixin
from app.modules.marketplace.service.marketplace_workflow_mixin import MarketplaceWorkflowMixin
from app.modules.marketplace.service.payout_manager import MarketplacePayoutManager
from app.modules.marketplace.service.policy import price_lumens_from_rub
from app.modules.marketplace.service.review_service import MarketplaceReviewService

__all__ = ["MarketplaceService", "price_lumens_from_rub"]


class MarketplaceService(MarketplaceProjectionMixin, MarketplaceWorkflowMixin):
    def __init__(
        self,
        repo: MarketplaceRepository,
        billing_repo: BillingRepository,
        wallet_repo: WalletRepository,
        store_repo: StoreRepository,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._payouts = MarketplacePayoutManager(repo, wallet_repo)
        self._access = MarketplaceAccessService(repo, billing_repo, store_repo)
        self._reviews = MarketplaceReviewService(repo, self._review_to_read)
        self._checkout = MarketplaceCheckoutService(
            repo=repo,
            wallet_repo=wallet_repo,
            store_repo=store_repo,
            settings=settings,
            access_service=self._access,
            purchase_to_read=lambda purchase, can_review=None: self._purchase_to_read(purchase, can_review=can_review),
            sync_reserved_payout=self._payouts.sync_reserved_payout,
        )
