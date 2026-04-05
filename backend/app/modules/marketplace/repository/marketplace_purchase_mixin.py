from __future__ import annotations

from app.modules.marketplace.repository.marketplace_plan_usage_mixin import MarketplacePlanUsageMixin
from app.modules.marketplace.repository.marketplace_purchase_lookup_mixin import MarketplacePurchaseLookupMixin
from app.modules.marketplace.repository.marketplace_purchase_write_mixin import MarketplacePurchaseWriteMixin


class MarketplacePurchaseMixin(
    MarketplacePurchaseWriteMixin,
    MarketplacePlanUsageMixin,
    MarketplacePurchaseLookupMixin,
):
    """Composed purchase and plan-usage persistence mixin."""

