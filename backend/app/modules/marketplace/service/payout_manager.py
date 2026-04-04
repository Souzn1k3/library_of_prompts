from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import inspect as sa_inspect

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
    PromptPurchase,
    PurchaseStatus,
)
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.model.marketplace import MarketplacePayoutRead
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.policy import ALLOWED_PAYOUT_CURRENCIES


class MarketplacePayoutManager:
    def __init__(self, repo: MarketplaceRepository, wallet_repo: WalletRepository) -> None:
        self._repo = repo
        self._wallet = wallet_repo

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

    async def refresh_settlement_states(
        self,
        *,
        seller_user_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> int:
        now = now or datetime.now(timezone.utc)
        released = 0
        rows = await self._repo.list_settlement_ready_purchases(
            seller_user_id=seller_user_id,
            now=now,
            for_update=True,
        )
        for purchase in rows:
            purchase.settlement_status = MarketplaceSettlementStatus.available
            await self._repo.save_purchase(purchase)
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_available,
                currency_code="LMN" if purchase.seller_amount_lumens > 0 else "RUB",
                amount=max(purchase.seller_amount_lumens, purchase.seller_amount_rub),
                meta={"purchase_id": str(purchase.id)},
            )
            released += 1
        return released

    async def create_payout_batch(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        notes: str | None = None,
    ) -> MarketplacePayoutRead:
        normalized_currency = self.normalize_payout_currency(currency_code)
        await self.refresh_settlement_states(seller_user_id=seller_user_id)
        purchases = await self._repo.list_available_purchases_for_payout(
            seller_user_id=seller_user_id,
            currency_code=normalized_currency,
            for_update=True,
        )
        if not purchases:
            raise AppError(
                code="no_payout_balance",
                message="There are no available earnings ready for payout.",
                status_code=409,
            )
        total_amount = sum(self.seller_amount_for_currency(purchase, normalized_currency) for purchase in purchases)
        payout = await self._repo.create_payout(
            seller_user_id=seller_user_id,
            currency_code=normalized_currency,
            total_amount=total_amount,
            purchase_count=len(purchases),
            notes=notes,
        )
        for purchase in purchases:
            purchase.payout_id = payout.id
            await self._repo.save_purchase(purchase)
        payout = await self.sync_reserved_payout(payout)
        return self.payout_to_read(payout)

    async def mark_payout_processing(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            return self.payout_to_read(payout)
        if payout.status in {MarketplacePayoutStatus.failed, MarketplacePayoutStatus.canceled}:
            raise AppError(
                code="payout_not_processable",
                message="This payout can no longer be processed.",
                status_code=409,
            )
        payout = await self.sync_reserved_payout(payout)
        if payout.purchase_count <= 0:
            raise AppError(
                code="payout_empty",
                message="This payout no longer has eligible earnings attached.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.processing
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)

    async def fail_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be failed.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.failed
        await self.release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)

    async def cancel_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be canceled.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.canceled
        await self.release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)

    async def finalize_payout(
        self,
        *,
        payout_id: uuid.UUID,
        reference: str | None = None,
        now: datetime | None = None,
    ) -> MarketplacePayoutRead:
        now = now or datetime.now(timezone.utc)
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            return self.payout_to_read(payout)
        if payout.status in {MarketplacePayoutStatus.failed, MarketplacePayoutStatus.canceled}:
            raise AppError(
                code="payout_not_payable",
                message="This payout is no longer payable.",
                status_code=409,
            )
        payout = await self.sync_reserved_payout(payout)
        eligible_purchases = self.eligible_payout_purchases(payout)
        if not eligible_purchases:
            raise AppError(
                code="payout_empty",
                message="This payout no longer has eligible earnings attached.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.paid
        payout.external_reference = reference
        payout.paid_at = now
        payout.purchase_count = len(eligible_purchases)
        payout.total_amount = sum(
            self.seller_amount_for_currency(purchase, payout.currency_code)
            for purchase in eligible_purchases
        )
        for purchase in eligible_purchases:
            purchase.settlement_status = MarketplaceSettlementStatus.paid_out
            purchase.paid_out_at = now
            await self._repo.save_purchase(purchase)
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_payout,
                currency_code=payout.currency_code,
                amount=self.seller_amount_for_currency(purchase, payout.currency_code),
                meta={"purchase_id": str(purchase.id), "payout_id": str(payout.id)},
            )
        await self._repo.save_payout(payout)
        if payout.currency_code.upper() == "LMN" and payout.seller_user_id is not None and payout.total_amount > 0:
            await self._wallet.adjust_balance(
                user_id=payout.seller_user_id,
                amount=payout.total_amount,
                reason=CurrencyTransactionType.marketplace_sale,
                context=f"marketplace:payout:{payout.id}",
                source_id=payout.id,
                metadata={"payout_id": str(payout.id), "currency_code": payout.currency_code},
                now=now,
            )
        return self.payout_to_read(payout)
