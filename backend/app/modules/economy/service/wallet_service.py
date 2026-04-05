from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.wallet_actions_mixin import WalletActionsMixin
from app.modules.economy.service.wallet_benefit_resolver import WalletBenefitResolver
from app.modules.economy.service.wallet_goal_planner import WalletGoalPlanner
from app.modules.economy.service.wallet_read_mixin import WalletReadMixin
from app.modules.economy.service.wallet_support_mixin import WalletSupportMixin


class WalletService(WalletSupportMixin, WalletReadMixin, WalletActionsMixin):
    def __init__(
        self,
        repo: WalletRepository,
        store_repo: StoreRepository | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._store_repo = store_repo
        self._analytics = analytics
        self._benefit_resolver = WalletBenefitResolver(repo=repo, store_repo=store_repo)
        self._goal_planner = WalletGoalPlanner(repo=repo, store_repo=store_repo)
