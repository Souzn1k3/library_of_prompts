from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.payout_batch_mixin import MarketplacePayoutBatchMixin
from app.modules.marketplace.service.payout_status_mixin import MarketplacePayoutStatusMixin
from app.modules.marketplace.service.payout_support_mixin import MarketplacePayoutSupportMixin


class MarketplacePayoutManager(
    MarketplacePayoutSupportMixin,
    MarketplacePayoutBatchMixin,
    MarketplacePayoutStatusMixin,
):
    def __init__(self, repo: MarketplaceRepository, wallet_repo: WalletRepository) -> None:
        self._repo = repo
        self._wallet = wallet_repo
