from __future__ import annotations

import uuid
from datetime import datetime

from app.infrastructure.db.models import PlanTier, PlanUsageWindow
from sqlalchemy import select


class MarketplacePlanUsageMixin:
    @staticmethod
    def _build_plan_usage_window_row(
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        included_paid_prompt_limit: int,
        used_paid_prompt_unlocks: int,
    ) -> PlanUsageWindow:
        return PlanUsageWindow(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_paid_prompt_limit,
            used_paid_prompt_unlocks=used_paid_prompt_unlocks,
        )

    async def get_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        for_update: bool = False,
    ) -> PlanUsageWindow | None:
        stmt = select(PlanUsageWindow).where(
            PlanUsageWindow.user_id == user_id,
            PlanUsageWindow.plan_tier == plan_tier,
            PlanUsageWindow.window_started_at == window_started_at,
            PlanUsageWindow.window_ends_at == window_ends_at,
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        included_paid_prompt_limit: int,
        used_paid_prompt_unlocks: int = 0,
    ) -> PlanUsageWindow:
        row = self._build_plan_usage_window_row(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_paid_prompt_limit,
            used_paid_prompt_unlocks=used_paid_prompt_unlocks,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def try_create_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        included_paid_prompt_limit: int,
        used_paid_prompt_unlocks: int = 0,
    ) -> PlanUsageWindow | None:
        row = self._build_plan_usage_window_row(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_paid_prompt_limit,
            used_paid_prompt_unlocks=used_paid_prompt_unlocks,
        )
        return await self._try_insert_unique(row)

    async def save_plan_usage_window(self, row: PlanUsageWindow) -> PlanUsageWindow:
        await self._session.flush()
        await self._session.refresh(row)
        return row
