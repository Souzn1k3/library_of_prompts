from __future__ import annotations

import uuid

from app.core.tiers import is_staff
from app.infrastructure.db.models import Prompt, PromptAccessSource, User
from app.modules.marketplace.model.marketplace import CatalogAction, PromptAccessRead


class MarketplaceAccessResolutionMixin:
    async def build_access_map(self, rows: list[Prompt], viewer: User | None) -> dict[uuid.UUID, PromptAccessRead]:
        if not rows:
            return {}
        prompt_ids = [row.id for row in rows]
        prices = await self._repo.list_prompt_prices(prompt_ids)
        if viewer is None:
            return {
                row.id: PromptAccessRead(
                    has_access=False,
                    purchase_required=True,
                    catalog_action=CatalogAction.signin,
                )
                for row in rows
                if prices.get(row.id) is not None and prices[row.id].is_active
            }
        entitled_ids = await self._repo.list_entitled_prompt_ids(user_id=viewer.id, prompt_ids=prompt_ids)
        legacy_owned_ids = await self._store.list_owned_prompt_ids(user_id=viewer.id, prompt_ids=prompt_ids)
        plan_context = await self.get_plan_access_context(viewer)
        out: dict[uuid.UUID, PromptAccessRead] = {}
        for row in rows:
            price = prices.get(row.id)
            if price is None or not price.is_active:
                continue
            if row.author_id == viewer.id:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.author.value)
                continue
            if is_staff(viewer):
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.staff.value)
                continue
            if row.id in entitled_ids:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                continue
            if row.id in legacy_owned_ids:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.legacy_store.value)
                continue
            if plan_context.remaining_unlocks > 0:
                out[row.id] = PromptAccessRead(
                    has_access=False,
                    can_unlock_with_plan=True,
                    remaining_plan_unlocks=plan_context.remaining_unlocks,
                    monthly_plan_unlocks=plan_context.total_unlocks,
                    catalog_action=CatalogAction.open,
                )
            else:
                out[row.id] = PromptAccessRead(
                    has_access=False,
                    purchase_required=True,
                    monthly_plan_unlocks=plan_context.total_unlocks,
                    catalog_action=CatalogAction.buy,
                )
        return out

    async def resolve_prompt_access(
        self,
        prompt: Prompt,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = False,
    ) -> PromptAccessRead:
        price = prompt.pricing
        if price is None or not price.is_active:
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.free.value)
        if viewer is None:
            return PromptAccessRead(
                has_access=False,
                purchase_required=True,
                catalog_action=CatalogAction.signin,
            )
        viewer_id = viewer.id
        viewer_plan_tier = viewer.plan_tier
        if prompt.author_id == viewer_id:
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.author.value)
        prompt_id = prompt.id
        seller_user_id = prompt.author_id
        if is_staff(viewer):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.staff.value)
        entitlement = await self._repo.get_entitlement(
            user_id=viewer_id,
            prompt_id=prompt_id,
            for_update=auto_grant_included_unlock,
        )
        if entitlement is not None:
            return PromptAccessRead(has_access=True, is_owned=True, source=entitlement.source.value)
        if await self._store.user_has_prompt_access(user_id=viewer_id, prompt_id=prompt_id):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.legacy_store.value)
        plan_context = await self._get_plan_access_context(
            user_id=viewer_id,
            plan_tier=viewer_plan_tier,
            for_update=auto_grant_included_unlock,
        )
        if plan_context.remaining_unlocks <= 0:
            return PromptAccessRead(
                has_access=False,
                purchase_required=True,
                remaining_plan_unlocks=0,
                monthly_plan_unlocks=plan_context.total_unlocks,
                catalog_action=CatalogAction.buy,
            )
        if not auto_grant_included_unlock:
            return PromptAccessRead(
                has_access=False,
                can_unlock_with_plan=True,
                remaining_plan_unlocks=plan_context.remaining_unlocks,
                monthly_plan_unlocks=plan_context.total_unlocks,
                catalog_action=CatalogAction.open,
            )
        await self._grant_included_unlock(
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            user_id=viewer_id,
            plan_tier=viewer_plan_tier,
            plan_context=plan_context,
        )
        return PromptAccessRead(
            has_access=True,
            is_owned=True,
            source=PromptAccessSource.subscription_limit.value,
            can_unlock_with_plan=True,
            remaining_plan_unlocks=max(plan_context.remaining_unlocks - 1, 0),
            monthly_plan_unlocks=plan_context.total_unlocks,
        )
