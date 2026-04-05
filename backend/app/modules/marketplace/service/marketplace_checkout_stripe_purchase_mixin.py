from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.tiers import is_staff
from app.infrastructure.db.models import (
    PromptAccessSource,
    PromptPaymentMethod,
    PromptPurchase,
    PurchaseStatus,
    User,
)
from app.modules.marketplace.model.marketplace import PromptCheckoutSessionRequest, PromptCheckoutSessionResponse
from app.modules.marketplace.service.marketplace_checkout_shared import stripe
from app.modules.marketplace.service.policy import append_query, apply_discount, fee


class MarketplaceCheckoutStripePurchaseMixin:
    async def create_checkout_session(
        self,
        *,
        user: User,
        payload: PromptCheckoutSessionRequest,
    ) -> PromptCheckoutSessionResponse:
        token_prefix = "mkt-checkout"
        user_id = user.id
        staff_user = is_staff(user)
        prompt = await self._repo.get_prompt_by_id(payload.prompt_id)
        if prompt is None:
            raise NotFoundError("prompt", str(payload.prompt_id))
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        prompt_id = prompt.id
        prompt_slug = prompt.slug
        prompt_title = prompt.title
        prompt_summary = prompt.summary or "Paid prompt unlock"
        seller_user_id = prompt.author_id
        base_price_rub = int(prompt.pricing.price_rub)
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
                raise ConflictError("This prompt is already purchased.")
        active_purchase = await self._repo.get_active_purchase(user_id=user_id, prompt_id=prompt_id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")
        effective_client_token = self._scoped_client_token(user_id, payload.client_token, prefix=token_prefix)
        plan_context = await self._access.get_plan_access_context(user)
        effective_price_rub = apply_discount(base_price_rub, plan_context.money_discount_percent)
        fee_rub = fee(effective_price_rub)
        seller_rub = max(effective_price_rub - fee_rub, 0)
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.stripe,
            status=PurchaseStatus.pending,
            price_rub=effective_price_rub,
            price_lumens=0,
            platform_fee_rub=fee_rub,
            seller_amount_rub=seller_rub,
            client_token=effective_client_token,
            meta={"base_price_rub": base_price_rub},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                raise ConflictError("This prompt is already purchased.")
            raise ConflictError("A purchase for this prompt is already being processed.")
        success_url = self._resolve_checkout_redirect_url(
            payload.success_url,
            default_url=append_query(self._settings.billing_checkout_success_url, prompt=prompt_slug),
        )
        cancel_url = self._resolve_checkout_redirect_url(
            payload.cancel_url,
            default_url=self._settings.billing_checkout_cancel_url,
        )
        if self._settings.billing_mock_mode or not self._stripe_checkout_enabled():
            completed_at = datetime.now(timezone.utc)
            settlement_status, settlement_available_at = self._initial_settlement_status(
                seller_amount_rub=seller_rub,
                seller_amount_lumens=0,
                completed_at=completed_at,
            )
            purchase.status = PurchaseStatus.completed
            purchase.completed_at = completed_at
            purchase.settlement_status = settlement_status
            purchase.settlement_available_at = settlement_available_at
            purchase.meta = {**(purchase.meta or {}), "mock": True}
            await self._repo.save_purchase(purchase)
            await self._ensure_purchase_entitlement(
                user_id=user_id,
                prompt_id=prompt_id,
                purchase_id=purchase.id,
                source=PromptAccessSource.direct_money,
                payment_method=PromptPaymentMethod.stripe.value,
                granted_at=completed_at,
                meta={"mock": True},
            )
            await self._record_purchase_transactions(
                purchase_id=purchase.id,
                prompt_id=prompt_id,
                buyer_user_id=user_id,
                seller_user_id=seller_user_id,
                currency_code="RUB",
                buyer_amount=effective_price_rub,
                fee_amount=fee_rub,
                seller_amount=seller_rub,
                meta={"prompt_id": str(prompt_id), "mock": True},
            )
            return PromptCheckoutSessionResponse(
                url=success_url,
                session_id=f"mock_prompt_{purchase.id.hex}",
                purchase_id=purchase.id,
            )
        assert stripe is not None
        stripe.api_key = self._settings.stripe_secret_key
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "rub",
                        "unit_amount": effective_price_rub * 100,
                        "product_data": {
                            "name": prompt_title,
                            "description": prompt_summary,
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user_id),
            metadata={
                "kind": "prompt_purchase",
                "purchase_id": str(purchase.id),
                "prompt_id": str(prompt_id),
                "user_id": str(user_id),
            },
            payment_intent_data={
                "metadata": {
                    "kind": "prompt_purchase",
                    "purchase_id": str(purchase.id),
                    "prompt_id": str(prompt_id),
                    "user_id": str(user_id),
                }
            },
        )
        purchase.provider_checkout_id = str(getattr(session, "id", None) or session.get("id"))
        await self._repo.save_purchase(purchase)
        return PromptCheckoutSessionResponse(
            url=str(getattr(session, "url", None) or session.get("url")),
            session_id=purchase.provider_checkout_id,
            purchase_id=purchase.id,
        )

    async def complete_checkout_purchase(
        self,
        *,
        checkout_id: str,
        payment_id: str | None = None,
        completed_at: datetime | None = None,
    ) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_checkout_id(checkout_id)
        if purchase is None:
            return None
        if purchase.status == PurchaseStatus.completed:
            return purchase
        completed_at = completed_at or datetime.now(timezone.utc)
        settlement_status, settlement_available_at = self._initial_settlement_status(
            seller_amount_rub=purchase.seller_amount_rub,
            seller_amount_lumens=0,
            completed_at=completed_at,
        )
        purchase.status = PurchaseStatus.completed
        purchase.provider_payment_id = payment_id or purchase.provider_payment_id
        purchase.completed_at = completed_at
        purchase.settlement_status = settlement_status
        purchase.settlement_available_at = settlement_available_at
        await self._repo.save_purchase(purchase)
        await self._ensure_purchase_entitlement(
            user_id=purchase.user_id,
            prompt_id=purchase.prompt_id,
            purchase_id=purchase.id,
            source=PromptAccessSource.direct_money,
            payment_method=PromptPaymentMethod.stripe.value,
            granted_at=completed_at,
        )
        await self._record_purchase_transactions(
            purchase_id=purchase.id,
            prompt_id=purchase.prompt_id,
            buyer_user_id=purchase.user_id,
            seller_user_id=purchase.seller_user_id,
            currency_code="RUB",
            buyer_amount=purchase.price_rub,
            fee_amount=purchase.platform_fee_rub,
            seller_amount=purchase.seller_amount_rub,
            meta={"purchase_id": str(purchase.id)},
        )
        return purchase

    async def fail_checkout_purchase(self, *, checkout_id: str, reason: str) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_checkout_id(checkout_id)
        if purchase is None or purchase.status != PurchaseStatus.pending:
            return purchase
        purchase.status = PurchaseStatus.failed
        purchase.meta = {**(purchase.meta or {}), "failure_reason": reason}
        await self._repo.save_purchase(purchase)
        return purchase

    async def fail_checkout_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_id(purchase_id)
        if purchase is None or purchase.status != PurchaseStatus.pending:
            return purchase
        purchase.status = PurchaseStatus.failed
        purchase.meta = {**(purchase.meta or {}), "failure_reason": reason}
        await self._repo.save_purchase(purchase)
        return purchase
