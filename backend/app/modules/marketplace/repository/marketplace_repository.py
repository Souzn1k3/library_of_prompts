from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.marketplace.repository.marketplace_base_mixin import MarketplaceBaseMixin
from app.modules.marketplace.repository.marketplace_payout_mixin import MarketplacePayoutMixin
from app.modules.marketplace.repository.marketplace_price_entitlement_mixin import MarketplacePriceEntitlementMixin
from app.modules.marketplace.repository.marketplace_prompt_mixin import MarketplacePromptMixin
from app.modules.marketplace.repository.marketplace_purchase_mixin import MarketplacePurchaseMixin
from app.modules.marketplace.repository.marketplace_review_mixin import MarketplaceReviewMixin


class MarketplaceRepository(
    MarketplacePromptMixin,
    MarketplaceReviewMixin,
    MarketplacePayoutMixin,
    MarketplacePurchaseMixin,
    MarketplacePriceEntitlementMixin,
    MarketplaceBaseMixin,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
