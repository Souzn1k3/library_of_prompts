from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import AppError, ConflictError
from app.core.tiers import is_staff
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    Prompt,
    PromptAccessSource,
    PromptPaymentMethod,
    PurchaseStatus,
    User,
)
from app.modules.marketplace.model.marketplace import (
    PromptAccessRead,
    PromptLumenPurchaseRequest,
    PromptPurchaseActionResponse,
)
from app.modules.marketplace.service.policy import apply_discount, fee


class MarketplaceCheckoutLumenPurchaseMixin:
    async def purchase_with_lumens(
        self,
        *,
        user: User,
        prompt: Prompt,
        payload: PromptLumenPurchaseRequest,
    ) -> PromptPurchaseActionResponse:
        token_prefix = "mkt-lmn"
        user_id = user.id
        staff_user = is_staff(user)
        prompt_id = prompt.id
        seller_user_id = prompt.author_id
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        base_price_lumens = int(prompt.pricing.price_lumens)
        if seller_user_id == user_id:
            raise AppError(code="cannot_buy_own_prompt", message="You can't buy your own prompt.", status_code=400)
        if staff_user:
            raise ConflictError("You already own this prompt.")
        entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id)
        if entitlement is not None or await self._store.user_has_prompt_access(user_id=user_id, prompt_id=prompt_id):
            raise ConflictError("You already own this prompt.")

        if payload.client_token:
            existing = await self._find_purchase_by_client_token(
                user_id=user_id,
                client_token=payload.client_token,
                prefix=token_prefix,
            )
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                return PromptPurchaseActionResponse(purchase=self._to_purchase_read(existing), access=access)

        active_purchase = await self._repo.get_active_purchase(user_id=user_id, prompt_id=prompt_id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")

        effective_client_token = self._scoped_client_token(user_id, payload.client_token, prefix=token_prefix)
        plan_context = await self._access.get_plan_access_context(user)
        effective_price_lumens = apply_discount(base_price_lumens, plan_context.lumen_discount_percent)
        fee_lumens = fee(effective_price_lumens)
        seller_lumens = max(effective_price_lumens - fee_lumens, 0)
        now = datetime.now(timezone.utc)
        settlement_status, settlement_available_at = self._initial_settlement_status(
            seller_amount_rub=0,
            seller_amount_lumens=seller_lumens,
            completed_at=now,
        )
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.lumens,
            status=PurchaseStatus.pending,
            settlement_status=settlement_status,
            price_rub=0,
            price_lumens=effective_price_lumens,
            platform_fee_lumens=fee_lumens,
            seller_amount_lumens=seller_lumens,
            settlement_available_at=settlement_available_at,
            client_token=effective_client_token,
            meta={"base_price_lumens": base_price_lumens},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                return PromptPurchaseActionResponse(purchase=self._to_purchase_read(existing), access=access)
            raise ConflictError("A purchase for this prompt is already being processed.")
        prompt_row = await self._repo.get_prompt_by_id(prompt_id)
        if prompt_row is not None:
            purchase.prompt = prompt_row
        await self._wallet.adjust_balance(
            user_id=user_id,
            amount=-effective_price_lumens,
            reason=CurrencyTransactionType.marketplace_purchase,
            context=f"prompt:{prompt_id}:purchase:{purchase.id}:buyer",
            source_id=purchase.id,
            metadata={"prompt_id": str(prompt_id), "purchase_id": str(purchase.id)},
            now=now,
        )
        purchase.status = PurchaseStatus.completed
        purchase.completed_at = now
        await self._repo.save_purchase(purchase)
        await self._ensure_purchase_entitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            purchase_id=purchase.id,
            source=PromptAccessSource.direct_lumens,
            payment_method=PromptPaymentMethod.lumens.value,
            granted_at=now,
        )
        await self._record_purchase_transactions(
            purchase_id=purchase.id,
            prompt_id=prompt_id,
            buyer_user_id=user_id,
            seller_user_id=seller_user_id,
            currency_code="LMN",
            buyer_amount=effective_price_lumens,
            fee_amount=fee_lumens,
            seller_amount=seller_lumens,
            meta={"prompt_id": str(prompt_id)},
        )
        access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
        return PromptPurchaseActionResponse(
            purchase=self._to_purchase_read(purchase, can_review=True),
            access=access,
        )
