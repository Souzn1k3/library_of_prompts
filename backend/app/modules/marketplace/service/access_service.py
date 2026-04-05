from __future__ import annotations

from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.access_plan_mixin import MarketplaceAccessPlanMixin
from app.modules.marketplace.service.access_resolution_mixin import MarketplaceAccessResolutionMixin
from app.modules.marketplace.service.access_types import PlanAccessContext
from app.modules.marketplace.service.access_unlock_mixin import MarketplaceAccessUnlockMixin

__all__ = ["MarketplaceAccessService", "PlanAccessContext"]


class MarketplaceAccessService(
    MarketplaceAccessPlanMixin,
    MarketplaceAccessResolutionMixin,
    MarketplaceAccessUnlockMixin,
):
    def __init__(
        self,
        repo: MarketplaceRepository,
        billing_repo: BillingRepository,
        store_repo: StoreRepository,
    ) -> None:
        self._repo = repo
        self._billing = billing_repo
        self._store = store_repo
