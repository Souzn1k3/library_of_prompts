from __future__ import annotations

from app.modules.marketplace.service.marketplace_checkout_lumen_purchase_mixin import (
    MarketplaceCheckoutLumenPurchaseMixin,
)
from app.modules.marketplace.service.marketplace_checkout_stripe_purchase_mixin import (
    MarketplaceCheckoutStripePurchaseMixin,
)


class MarketplaceCheckoutPurchaseMixin(
    MarketplaceCheckoutStripePurchaseMixin,
    MarketplaceCheckoutLumenPurchaseMixin,
):
    """Composed checkout purchase mixin split by payment flow."""

