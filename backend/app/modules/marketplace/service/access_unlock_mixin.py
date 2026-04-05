from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.errors import AppError
from app.infrastructure.db.models import (
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
    PlanTier,
    PromptAccessSource,
    PromptPaymentMethod,
    PromptPurchase,
    PurchaseStatus,
)
from app.modules.marketplace.service.access_types import PlanAccessContext


class MarketplaceAccessUnlockMixin:
    async def _grant_included_unlock(
        self,
        *,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        plan_context: PlanAccessContext,
    ) -> PromptPurchase:
        if plan_context.remaining_unlocks <= 0:
            raise AppError(
                code="plan_unlocks_exhausted",
                message="You've used all included paid prompt unlocks for the current period.",
                status_code=402,
            )
        window_started_at, window_ends_at = await self._resolve_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
        )
        usage = await self._get_or_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=True,
        )
        if usage.used_paid_prompt_unlocks >= usage.included_paid_prompt_limit:
            raise AppError(
                code="plan_unlocks_exhausted",
                message="You've used all included paid prompt unlocks for the current period.",
                status_code=402,
            )
        plan_token = f"plan-{user_id}-{prompt_id}"
        now = datetime.now(timezone.utc)
        created_purchase = True
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.included_limit,
            status=PurchaseStatus.completed,
            settlement_status=MarketplaceSettlementStatus.available,
            price_rub=0,
            price_lumens=0,
            client_token=plan_token,
            settlement_available_at=now,
            completed_at=now,
            meta={"included_unlock": True, "plan_tier": plan_tier.value},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=plan_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                created_purchase = False
                purchase = existing
            else:
                raise RuntimeError("Included unlock purchase insert conflicted but existing row was not found.")

        entitlement = await self._repo.try_create_entitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=PromptAccessSource.subscription_limit,
            purchase_id=purchase.id,
            meta={"plan_tier": plan_tier.value},
            granted_at=now,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id, for_update=True)
            if entitlement is None:
                raise

        # Retries/concurrency that resolve to existing purchase+entitlement must not spend quota twice.
        if not created_purchase or entitlement.purchase_id != purchase.id:
            return purchase

        usage.used_paid_prompt_unlocks += 1
        await self._repo.save_plan_usage_window(usage)
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt_id,
            actor_user_id=user_id,
            kind=MarketplaceTransactionKind.included_unlock,
            currency_code="PLAN",
            amount=1,
            meta={"plan_tier": plan_tier.value},
        )
        return purchase
