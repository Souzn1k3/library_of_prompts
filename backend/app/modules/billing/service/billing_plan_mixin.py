from __future__ import annotations

from app.infrastructure.db.models import Plan, PlanTier, User
from app.modules.billing.model.billing import BillingStatusRead, PlanPublicRead
from app.modules.billing.service.billing_stripe_client import stripe


class BillingPlanMixin:
    def _copy_for_language(self, language: str | None) -> dict[PlanTier, dict[str, object]]:
        if language and language in self._PLAN_COPY:
            return self._PLAN_COPY[language]
        return self._PLAN_COPY["en"]

    async def list_public_plans(self, language: str | None) -> list[PlanPublicRead]:
        rows = await self._repo.list_active_plans()
        copy = self._copy_for_language(language)
        items: list[PlanPublicRead] = []
        for row in rows:
            localized = copy.get(row.tier, {})
            highlights_raw = localized.get("highlights")
            full_features_raw = localized.get("full_features")
            items.append(
                PlanPublicRead(
                    tier=row.tier,
                    name=str(localized.get("name") or row.name),
                    description=row.description,
                    price_usd_month=row.price_usd_month,
                    price_rub_month=row.price_rub_month,
                    monthly_paid_prompt_limit=row.monthly_paid_prompt_limit,
                    prompt_purchase_discount_percent=row.prompt_purchase_discount_percent,
                    lumen_purchase_discount_percent=row.lumen_purchase_discount_percent,
                    highlights=list(highlights_raw) if isinstance(highlights_raw, list) else [],
                    full_features=list(full_features_raw) if isinstance(full_features_raw, list) else [],
                    sort_order=row.sort_order,
                    is_active=row.is_active,
                )
            )
        return items

    async def get_subscription_status(self, user: User) -> BillingStatusRead:
        latest = await self._repo.get_latest_subscription_for_user(user.id)
        access = await self._marketplace.get_plan_access_context(user) if self._marketplace is not None else None
        return BillingStatusRead(
            plan_tier=user.plan_tier,
            subscription_tier=latest.plan.tier if latest and latest.plan else None,
            provider=latest.provider if latest else None,
            status=latest.status if latest else None,
            current_period_end=latest.current_period_end if latest else None,
            cancel_at_period_end=latest.cancel_at_period_end if latest else False,
            updated_at=latest.updated_at if latest else None,
            paid_prompt_limit_total=access.total_unlocks if access is not None else 0,
            paid_prompt_limit_remaining=access.remaining_unlocks if access is not None else 0,
            prompt_purchase_discount_percent=access.money_discount_percent if access is not None else 0,
            lumen_purchase_discount_percent=access.lumen_discount_percent if access is not None else 0,
        )

    def _resolve_price_id(self, plan: Plan) -> str | None:
        if plan.stripe_price_id:
            return plan.stripe_price_id
        by_tier = {
            PlanTier.starter: self._settings.stripe_price_starter,
            PlanTier.pro: self._settings.stripe_price_pro,
            PlanTier.enterprise: self._settings.stripe_price_enterprise,
        }
        return by_tier.get(plan.tier)

    def _stripe_checkout_enabled_for_plan(self, plan: Plan) -> bool:
        return bool(stripe and self._settings.stripe_secret_key and self._resolve_price_id(plan))

    def _stripe_webhook_enabled(self) -> bool:
        return bool(stripe and self._settings.stripe_secret_key and self._settings.stripe_webhook_secret)
