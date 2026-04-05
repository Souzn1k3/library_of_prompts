from __future__ import annotations

import uuid
from datetime import datetime

from app.infrastructure.db.models import Prompt, PromptPurchase, User
from app.modules.marketplace.model.marketplace import (
    MarketplacePayoutRead,
    PromptAccessRead,
    PromptCheckoutSessionRequest,
    PromptCheckoutSessionResponse,
    PromptLumenPurchaseRequest,
    PromptPurchaseActionResponse,
    PromptReviewRead,
    PromptReviewReportWrite,
    PromptReviewWrite,
)
from app.modules.marketplace.service.access_service import PlanAccessContext


class MarketplaceWorkflowMixin:
    async def refresh_settlement_states(
        self,
        *,
        seller_user_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> int:
        return await self._payouts.refresh_settlement_states(
            seller_user_id=seller_user_id,
            now=now,
        )

    async def create_payout_batch(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        notes: str | None = None,
    ) -> MarketplacePayoutRead:
        return await self._payouts.create_payout_batch(
            seller_user_id=seller_user_id,
            currency_code=currency_code,
            notes=notes,
        )

    async def mark_payout_processing(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.mark_payout_processing(payout_id=payout_id)

    async def fail_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.fail_payout(payout_id=payout_id)

    async def cancel_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.cancel_payout(payout_id=payout_id)

    async def finalize_payout(
        self,
        *,
        payout_id: uuid.UUID,
        reference: str | None = None,
        now: datetime | None = None,
    ) -> MarketplacePayoutRead:
        return await self._payouts.finalize_payout(
            payout_id=payout_id,
            reference=reference,
            now=now,
        )

    async def get_plan_access_context(self, user: User, *, for_update: bool = False) -> PlanAccessContext:
        return await self._access.get_plan_access_context(user, for_update=for_update)

    async def build_access_map(self, rows: list[Prompt], viewer: User | None) -> dict[uuid.UUID, PromptAccessRead]:
        return await self._access.build_access_map(rows, viewer)

    async def resolve_prompt_access(
        self,
        prompt: Prompt,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = False,
    ) -> PromptAccessRead:
        return await self._access.resolve_prompt_access(
            prompt,
            viewer,
            auto_grant_included_unlock=auto_grant_included_unlock,
        )

    async def purchase_with_lumens(
        self,
        *,
        user: User,
        prompt: Prompt,
        payload: PromptLumenPurchaseRequest,
    ) -> PromptPurchaseActionResponse:
        return await self._checkout.purchase_with_lumens(
            user=user,
            prompt=prompt,
            payload=payload,
        )

    async def create_checkout_session(
        self,
        *,
        user: User,
        payload: PromptCheckoutSessionRequest,
    ) -> PromptCheckoutSessionResponse:
        return await self._checkout.create_checkout_session(
            user=user,
            payload=payload,
        )

    async def complete_checkout_purchase(
        self,
        *,
        checkout_id: str,
        payment_id: str | None = None,
        completed_at: datetime | None = None,
    ) -> PromptPurchase | None:
        return await self._checkout.complete_checkout_purchase(
            checkout_id=checkout_id,
            payment_id=payment_id,
            completed_at=completed_at,
        )

    async def fail_checkout_purchase(self, *, checkout_id: str, reason: str) -> PromptPurchase | None:
        return await self._checkout.fail_checkout_purchase(checkout_id=checkout_id, reason=reason)

    async def fail_checkout_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str) -> PromptPurchase | None:
        return await self._checkout.fail_checkout_purchase_by_id(purchase_id=purchase_id, reason=reason)

    async def refund_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str | None = None) -> PromptPurchase | None:
        return await self._checkout.refund_purchase_by_id(purchase_id=purchase_id, reason=reason)

    async def refund_checkout_purchase(self, *, payment_id: str, reason: str | None = None) -> PromptPurchase | None:
        return await self._checkout.refund_checkout_purchase(payment_id=payment_id, reason=reason)

    async def report_review(
        self,
        *,
        user: User,
        review_id: uuid.UUID,
        payload: PromptReviewReportWrite,
    ) -> PromptReviewRead:
        return await self._reviews.report_review(user=user, review_id=review_id, payload=payload)

    async def upsert_review(
        self,
        *,
        user: User,
        prompt_id: uuid.UUID,
        payload: PromptReviewWrite,
    ) -> PromptReviewRead:
        return await self._reviews.upsert_review(user=user, prompt_id=prompt_id, payload=payload)
