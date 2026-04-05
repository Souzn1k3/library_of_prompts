from __future__ import annotations

from app.modules.economy.service.store_purchase_reward_mixin import StorePurchaseRewardMixin
from app.modules.economy.service.store_purchase_runtime_mixin import StorePurchaseRuntimeMixin


class StorePurchaseFlowMixin(
    StorePurchaseRuntimeMixin,
    StorePurchaseRewardMixin,
):
    """Composed store purchase flow with isolated reward/runtime concerns."""

