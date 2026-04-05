from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.economy.repository.store_repo_item_mixin import StoreRepositoryItemMixin
from app.modules.economy.repository.store_repo_purchase_mixin import StoreRepositoryPurchaseMixin
from app.modules.economy.repository.store_repo_unlock_mixin import StoreRepositoryUnlockMixin


class StoreRepository(StoreRepositoryUnlockMixin, StoreRepositoryPurchaseMixin, StoreRepositoryItemMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
