from __future__ import annotations

from sqlalchemy import inspect as sa_inspect

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import (
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    PromptPurchase,
    PurchaseStatus,
)
from app.modules.marketplace.model.marketplace import MarketplacePayoutRead
from app.modules.marketplace.service.policy import ALLOWED_PAYOUT_CURRENCIES


class MarketplacePayoutSupportMixin:
    @staticmethod
    def normalize_payout_currency(currency_code: str) -> str:
        normalized = currency_code.strip().upper()
        if normalized not in ALLOWED_PAYOUT_CURRENCIES:
            raise AppError(
                code="invalid_payout_currency",
                message="Unsupported payout currency.",
                status_code=400,
                details={"allowed": sorted(ALLOWED_PAYOUT_CURRENCIES)},
            )
        return normalized

    @staticmethod
    def seller_amount_for_currency(purchase: PromptPurchase, currency_code: str) -> int:
        if currency_code.upper() == "LMN":
            return int(purchase.seller_amount_lumens or 0)
        return int(purchase.seller_amount_rub or 0)

    @staticmethod
    def payout_to_read(payout: MarketplacePayout) -> MarketplacePayoutRead:
        return MarketplacePayoutRead(
            id=payout.id,
            currency_code=payout.currency_code,
            status=payout.status,
            total_amount=payout.total_amount,
            purchase_count=payout.purchase_count,
            external_reference=payout.external_reference,
            requested_at=payout.requested_at,
            paid_at=payout.paid_at,
        )

    def eligible_payout_purchases(self, payout: MarketplacePayout) -> list[PromptPurchase]:
        return [
            purchase
            for purchase in payout.purchases
            if purchase.status == PurchaseStatus.completed
            and purchase.settlement_status == MarketplaceSettlementStatus.available
            and purchase.payout_id == payout.id
        ]

    async def sync_reserved_payout(self, payout: MarketplacePayout) -> MarketplacePayout:
        payout_state = sa_inspect(payout)
        if "purchases" in payout_state.unloaded:
            loaded_payout = await self._repo.get_payout_by_id(payout.id, for_update=True)
            if loaded_payout is None:
                raise NotFoundError("marketplace_payout", str(payout.id))
            payout = loaded_payout
        eligible = self.eligible_payout_purchases(payout)
        payout.purchase_count = len(eligible)
        payout.total_amount = sum(
            self.seller_amount_for_currency(purchase, payout.currency_code)
            for purchase in eligible
        )
        if payout.status in {MarketplacePayoutStatus.requested, MarketplacePayoutStatus.processing} and payout.purchase_count == 0:
            payout.status = MarketplacePayoutStatus.canceled
        payout = await self._repo.save_payout(payout)
        loaded_payout = await self._repo.get_payout_by_id(payout.id, for_update=True)
        if loaded_payout is None:
            raise NotFoundError("marketplace_payout", str(payout.id))
        return loaded_payout

    async def release_payout_reservations(self, payout: MarketplacePayout) -> None:
        for purchase in payout.purchases:
            if purchase.payout_id != payout.id:
                continue
            if purchase.settlement_status == MarketplaceSettlementStatus.paid_out:
                continue
            purchase.payout_id = None
            await self._repo.save_purchase(purchase)
