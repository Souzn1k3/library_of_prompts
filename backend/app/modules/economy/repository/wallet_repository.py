from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.economy.repository.wallet_balance_mixin import WalletBalanceMixin
from app.modules.economy.repository.wallet_reward_mixin import WalletRewardMixin
from app.modules.economy.repository.wallet_segment_mixin import WalletSegmentMixin
from app.modules.economy.repository.wallet_streak_mixin import WalletStreakMixin


class WalletRepository(WalletSegmentMixin, WalletRewardMixin, WalletStreakMixin, WalletBalanceMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
