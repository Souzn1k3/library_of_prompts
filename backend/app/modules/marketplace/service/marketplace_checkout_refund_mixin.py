from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
    PromptPurchase,
    PurchaseStatus,
    ReviewModerationStatus,
)


class MarketplaceCheckoutRefundMixin:
    async def refund_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str | None = None) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_id(purchase_id, for_update=True)
        if purchase is None:
            return None
        return await self._refund_purchase(purchase=purchase, reason=reason)

    async def refund_checkout_purchase(self, *, payment_id: str, reason: str | None = None) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_payment_id(payment_id)
        if purchase is None:
            return purchase
        return await self._refund_purchase(purchase=purchase, reason=reason)

    async def _refund_purchase(self, *, purchase: PromptPurchase, reason: str | None = None) -> PromptPurchase:
        if purchase.status == PurchaseStatus.refunded:
            return purchase
        now = datetime.now(timezone.utc)
        prior_settlement_status = purchase.settlement_status
        payout = None
        if purchase.payout_id is not None:
            payout = await self._repo.get_payout_by_id(purchase.payout_id, for_update=True)
        purchase.status = PurchaseStatus.refunded
        purchase.settlement_status = MarketplaceSettlementStatus.refunded
        purchase.refunded_at = now
        purchase.meta = {
            **(purchase.meta or {}),
            "refund_reason": reason,
            "prior_settlement_status": prior_settlement_status.value,
        }
        await self._repo.save_purchase(purchase)
        if payout is not None and payout.status in {MarketplacePayoutStatus.requested, MarketplacePayoutStatus.processing}:
            await self._sync_reserved_payout(payout)
        entitlement = await self._repo.get_entitlement(user_id=purchase.user_id, prompt_id=purchase.prompt_id, for_update=True)
        if entitlement is not None:
            entitlement.revoked_at = now
            entitlement.revoke_reason = reason or "refunded"
            await self._repo.save_entitlement(entitlement)
        review = await self._repo.get_review_by_purchase_id(purchase.id)
        if review is not None:
            review.is_visible = False
            review.moderation_status = ReviewModerationStatus.hidden
            review.moderation_reason = "refunded_purchase"
            review.hidden_at = now
            await self._repo.save_review(review)

        if purchase.price_lumens > 0:
            await self._wallet.adjust_balance(
                user_id=purchase.user_id,
                amount=purchase.price_lumens,
                reason=CurrencyTransactionType.refund,
                context=f"prompt:{purchase.prompt_id}:purchase:{purchase.id}:buyer_refund",
                source_id=purchase.id,
                metadata={"purchase_id": str(purchase.id), "reason": reason, "currency_code": "LMN"},
                now=now,
            )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=purchase.prompt_id,
            actor_user_id=purchase.user_id,
            kind=MarketplaceTransactionKind.refund,
            currency_code="LMN" if purchase.price_lumens > 0 else "RUB",
            amount=max(purchase.price_lumens, purchase.price_rub),
            meta={"purchase_id": str(purchase.id), "reason": reason},
        )
        if purchase.seller_user_id is not None and (purchase.seller_amount_rub > 0 or purchase.seller_amount_lumens > 0):
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_reversal,
                currency_code="LMN" if purchase.seller_amount_lumens > 0 else "RUB",
                amount=max(purchase.seller_amount_lumens, purchase.seller_amount_rub),
                meta={
                    "purchase_id": str(purchase.id),
                    "reason": reason,
                    "prior_settlement_status": prior_settlement_status.value,
                },
            )
        return purchase
