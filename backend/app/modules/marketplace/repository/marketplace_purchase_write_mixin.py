from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import (
    MarketplaceSettlementStatus,
    MarketplaceTransaction,
    MarketplaceTransactionKind,
    PromptPurchase,
    PurchaseStatus,
)


class MarketplacePurchaseWriteMixin:
    @staticmethod
    def _build_purchase_row(
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        payment_method: Any,
        status: PurchaseStatus,
        settlement_status: MarketplaceSettlementStatus,
        price_rub: int,
        price_lumens: int,
        platform_fee_rub: int,
        seller_amount_rub: int,
        platform_fee_lumens: int,
        seller_amount_lumens: int,
        settlement_available_at: datetime | None,
        paid_out_at: datetime | None,
        disputed_at: datetime | None,
        payout_id: uuid.UUID | None,
        provider_checkout_id: str | None,
        provider_payment_id: str | None,
        client_token: str | None,
        completed_at: datetime | None,
        refunded_at: datetime | None,
        meta: dict | None,
    ) -> PromptPurchase:
        return PromptPurchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=payment_method,
            status=status,
            settlement_status=settlement_status,
            price_rub=price_rub,
            price_lumens=price_lumens,
            platform_fee_rub=platform_fee_rub,
            seller_amount_rub=seller_amount_rub,
            platform_fee_lumens=platform_fee_lumens,
            seller_amount_lumens=seller_amount_lumens,
            settlement_available_at=settlement_available_at,
            paid_out_at=paid_out_at,
            disputed_at=disputed_at,
            payout_id=payout_id,
            provider_checkout_id=provider_checkout_id,
            provider_payment_id=provider_payment_id,
            client_token=client_token,
            completed_at=completed_at,
            refunded_at=refunded_at,
            meta=meta,
        )

    async def _try_insert_unique(self, row: Any) -> Any | None:
        try:
            async with self._session.begin_nested():
                self._session.add(row)
                await self._session.flush()
        except IntegrityError:
            return None
        await self._session.refresh(row)
        return row

    async def create_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        payment_method: Any,
        status: PurchaseStatus,
        settlement_status: MarketplaceSettlementStatus = MarketplaceSettlementStatus.pending,
        price_rub: int,
        price_lumens: int,
        platform_fee_rub: int = 0,
        seller_amount_rub: int = 0,
        platform_fee_lumens: int = 0,
        seller_amount_lumens: int = 0,
        settlement_available_at: datetime | None = None,
        paid_out_at: datetime | None = None,
        disputed_at: datetime | None = None,
        payout_id: uuid.UUID | None = None,
        provider_checkout_id: str | None = None,
        provider_payment_id: str | None = None,
        client_token: str | None = None,
        completed_at: datetime | None = None,
        refunded_at: datetime | None = None,
        meta: dict | None = None,
    ) -> PromptPurchase:
        purchase = self._build_purchase_row(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=payment_method,
            status=status,
            settlement_status=settlement_status,
            price_rub=price_rub,
            price_lumens=price_lumens,
            platform_fee_rub=platform_fee_rub,
            seller_amount_rub=seller_amount_rub,
            platform_fee_lumens=platform_fee_lumens,
            seller_amount_lumens=seller_amount_lumens,
            settlement_available_at=settlement_available_at,
            paid_out_at=paid_out_at,
            disputed_at=disputed_at,
            payout_id=payout_id,
            provider_checkout_id=provider_checkout_id,
            provider_payment_id=provider_payment_id,
            client_token=client_token,
            completed_at=completed_at,
            refunded_at=refunded_at,
            meta=meta,
        )
        self._session.add(purchase)
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase

    async def try_create_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        payment_method: Any,
        status: PurchaseStatus,
        settlement_status: MarketplaceSettlementStatus = MarketplaceSettlementStatus.pending,
        price_rub: int,
        price_lumens: int,
        platform_fee_rub: int = 0,
        seller_amount_rub: int = 0,
        platform_fee_lumens: int = 0,
        seller_amount_lumens: int = 0,
        settlement_available_at: datetime | None = None,
        paid_out_at: datetime | None = None,
        disputed_at: datetime | None = None,
        payout_id: uuid.UUID | None = None,
        provider_checkout_id: str | None = None,
        provider_payment_id: str | None = None,
        client_token: str | None = None,
        completed_at: datetime | None = None,
        refunded_at: datetime | None = None,
        meta: dict | None = None,
    ) -> PromptPurchase | None:
        purchase = self._build_purchase_row(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=payment_method,
            status=status,
            settlement_status=settlement_status,
            price_rub=price_rub,
            price_lumens=price_lumens,
            platform_fee_rub=platform_fee_rub,
            seller_amount_rub=seller_amount_rub,
            platform_fee_lumens=platform_fee_lumens,
            seller_amount_lumens=seller_amount_lumens,
            settlement_available_at=settlement_available_at,
            paid_out_at=paid_out_at,
            disputed_at=disputed_at,
            payout_id=payout_id,
            provider_checkout_id=provider_checkout_id,
            provider_payment_id=provider_payment_id,
            client_token=client_token,
            completed_at=completed_at,
            refunded_at=refunded_at,
            meta=meta,
        )
        return await self._try_insert_unique(purchase)

    async def save_purchase(self, purchase: PromptPurchase) -> PromptPurchase:
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase

    async def create_marketplace_transaction(
        self,
        *,
        prompt_purchase_id: uuid.UUID | None,
        prompt_id: uuid.UUID | None,
        actor_user_id: uuid.UUID | None,
        kind: MarketplaceTransactionKind,
        currency_code: str,
        amount: int,
        meta: dict | None = None,
    ) -> MarketplaceTransaction:
        row = MarketplaceTransaction(
            prompt_purchase_id=prompt_purchase_id,
            prompt_id=prompt_id,
            actor_user_id=actor_user_id,
            kind=kind,
            currency_code=currency_code,
            amount=amount,
            meta=meta,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row
