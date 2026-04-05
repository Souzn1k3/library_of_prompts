from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.infrastructure.db.models import PlanTier, SubscriptionStatus, User
from app.modules.marketplace.service.access_types import PlanAccessContext
from app.modules.marketplace.service.policy import ensure_aware, start_of_current_month


class MarketplaceAccessPlanMixin:
    async def _resolve_usage_window(self, *, user_id: uuid.UUID, plan_tier: PlanTier) -> tuple[datetime, datetime]:
        latest = await self._billing.get_latest_subscription_for_user(user_id)
        if (
            latest is not None
            and latest.plan is not None
            and latest.plan.tier == plan_tier
            and latest.status in {SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due}
        ):
            start = ensure_aware(latest.current_period_start)
            end = ensure_aware(latest.current_period_end)
            if start is not None and end is not None and end > start:
                return start, end
        return start_of_current_month(datetime.now(timezone.utc))

    async def _get_or_create_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        for_update: bool,
    ) -> Any:
        usage = await self._repo.get_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        if usage is not None:
            return usage

        plan = await self._billing.get_plan_by_tier(plan_tier)
        included_limit = int(plan.monthly_paid_prompt_limit) if plan is not None else 0
        created = await self._repo.try_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_limit,
        )
        if created is not None:
            return created
        usage = await self._repo.get_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        if usage is None:
            raise RuntimeError("Plan usage window insert conflicted but row was not found.")
        return usage

    async def _get_plan_access_context(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        for_update: bool = False,
    ) -> PlanAccessContext:
        plan = await self._billing.get_plan_by_tier(plan_tier)
        if plan is None:
            return PlanAccessContext()
        total_unlocks = int(plan.monthly_paid_prompt_limit or 0)
        money_discount_percent = int(plan.prompt_purchase_discount_percent or 0)
        lumen_discount_percent = int(plan.lumen_purchase_discount_percent or 0)
        window_started_at, window_ends_at = await self._resolve_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
        )
        usage = await self._get_or_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        used = int(usage.used_paid_prompt_unlocks or 0)
        return PlanAccessContext(
            total_unlocks=total_unlocks,
            remaining_unlocks=max(total_unlocks - used, 0),
            money_discount_percent=money_discount_percent,
            lumen_discount_percent=lumen_discount_percent,
        )

    async def get_plan_access_context(self, user: User, *, for_update: bool = False) -> PlanAccessContext:
        return await self._get_plan_access_context(
            user_id=user.id,
            plan_tier=user.plan_tier,
            for_update=for_update,
        )
