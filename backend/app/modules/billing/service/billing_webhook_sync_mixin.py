from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.infrastructure.db.models import BillingProvider, PlanTier, SubscriptionStatus
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.billing.service.billing_utils import safe_uuid, to_datetime_from_unix


class BillingWebhookSyncMixin:
    def _map_subscription_status(self, raw_status: str | None) -> SubscriptionStatus:
        mapping = {
            "incomplete": SubscriptionStatus.incomplete,
            "incomplete_expired": SubscriptionStatus.incomplete_expired,
            "trialing": SubscriptionStatus.trialing,
            "active": SubscriptionStatus.active,
            "past_due": SubscriptionStatus.past_due,
            "canceled": SubscriptionStatus.canceled,
            "unpaid": SubscriptionStatus.unpaid,
        }
        return mapping.get((raw_status or "").lower(), SubscriptionStatus.incomplete)

    async def _ensure_customer_mapping(
        self,
        *,
        user_id: uuid.UUID,
        provider_customer_id: str,
    ) -> None:
        existing = await self._repo.get_billing_customer_by_provider_customer_id(
            BillingProvider.stripe,
            provider_customer_id,
        )
        if existing is not None:
            return
        existing_for_user = await self._repo.get_billing_customer_for_user(
            user_id,
            provider=BillingProvider.stripe,
        )
        if existing_for_user is not None:
            return
        user = await self._users.get_by_id(user_id)
        if user is None:
            return
        await self._repo.create_billing_customer(
            user_id=user_id,
            provider=BillingProvider.stripe,
            provider_customer_id=provider_customer_id,
            email=user.email,
        )

    async def _sync_subscription_from_stripe(
        self,
        *,
        stripe_subscription: dict[str, Any],
        provider_event_id: str,
        event_type: str,
        occurred_at: datetime | None,
        fallback_user_id: uuid.UUID | None = None,
    ) -> None:
        provider_subscription_id = str(stripe_subscription.get("id") or "")
        if not provider_subscription_id:
            return
        existing_subscription = await self._repo.get_subscription_by_provider_subscription_id(
            BillingProvider.stripe,
            provider_subscription_id,
        )
        previous_period_end = existing_subscription.current_period_end if existing_subscription is not None else None

        provider_customer_id = str(stripe_subscription.get("customer") or "")
        user_id: uuid.UUID | None = None
        if provider_customer_id:
            customer = await self._repo.get_billing_customer_by_provider_customer_id(
                BillingProvider.stripe,
                provider_customer_id,
            )
            if customer is not None:
                user_id = customer.user_id
        if user_id is None:
            user_id = fallback_user_id
        if user_id is None:
            metadata = stripe_subscription.get("metadata") or {}
            user_id = safe_uuid(metadata.get("user_id"))
        if user_id is None:
            return

        if provider_customer_id:
            await self._ensure_customer_mapping(
                user_id=user_id,
                provider_customer_id=provider_customer_id,
            )

        price_id: str | None = None
        items = stripe_subscription.get("items") or {}
        data = items.get("data") if isinstance(items, dict) else None
        if isinstance(data, list) and data:
            first = data[0] or {}
            price = first.get("price") if isinstance(first, dict) else None
            if isinstance(price, dict):
                raw_price_id = price.get("id")
                if raw_price_id:
                    price_id = str(raw_price_id)

        plan = await self._repo.get_plan_by_stripe_price_id(price_id) if price_id else None
        if plan is None:
            tier_hint = (stripe_subscription.get("metadata") or {}).get("tier")
            tier = None
            if tier_hint in {t.value for t in PlanTier}:
                tier = PlanTier(str(tier_hint))
            if tier is not None:
                plan = await self._repo.get_plan_by_tier(tier)
        if plan is None:
            if existing_subscription is not None and existing_subscription.plan is not None:
                plan = existing_subscription.plan
        if plan is None:
            return

        subscription = await self._repo.upsert_subscription(
            user_id=user_id,
            plan_id=plan.id,
            provider=BillingProvider.stripe,
            provider_subscription_id=provider_subscription_id,
            status=self._map_subscription_status(stripe_subscription.get("status")),
            current_period_start=to_datetime_from_unix(stripe_subscription.get("current_period_start")),
            current_period_end=to_datetime_from_unix(stripe_subscription.get("current_period_end")),
            trial_end=to_datetime_from_unix(stripe_subscription.get("trial_end")),
            cancel_at_period_end=bool(stripe_subscription.get("cancel_at_period_end", False)),
            canceled_at=to_datetime_from_unix(stripe_subscription.get("canceled_at")),
            metadata_json=stripe_subscription,
        )
        await self._repo.create_subscription_event(
            subscription_id=subscription.id,
            user_id=user_id,
            provider=BillingProvider.stripe,
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=stripe_subscription,
            occurred_at=occurred_at,
        )
        await self._entitlements.recalculate_user_tier(user_id)

        if self._analytics is not None:
            subscription_metadata = stripe_subscription.get("metadata") or {}
            source_page = subscription_metadata.get("source_page") if isinstance(subscription_metadata, dict) else None
            scenario_slug = subscription_metadata.get("scenario_slug") if isinstance(subscription_metadata, dict) else None
            paywall_variant = subscription_metadata.get("paywall_variant") if isinstance(subscription_metadata, dict) else None
            pricing_variant = subscription_metadata.get("pricing_variant") if isinstance(subscription_metadata, dict) else None
            attribution = await self._analytics.get_user_last_touch_attribution(user_id=user_id)

            if subscription.status in {SubscriptionStatus.active, SubscriptionStatus.trialing}:
                period_end_marker = subscription.current_period_end.isoformat() if subscription.current_period_end else "none"
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.subscription_activated,
                    user_id=user_id,
                    metadata={
                        "provider": BillingProvider.stripe.value,
                        "plan_tier": plan.tier.value,
                        "subscription_status": subscription.status.value,
                        "provider_subscription_id": provider_subscription_id,
                        "source_page": source_page,
                        "scenario_slug": scenario_slug,
                        "paywall_variant": paywall_variant,
                        "pricing_variant": pricing_variant,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="subscription_sync",
                    event_id=f"stripe_subscription_activated:{provider_subscription_id}:{subscription.status.value}:{period_end_marker}",
                )

            if existing_subscription is None and subscription.status in {SubscriptionStatus.active, SubscriptionStatus.trialing}:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.subscription_started,
                    user_id=user_id,
                    metadata={
                        "provider": BillingProvider.stripe.value,
                        "plan_tier": plan.tier.value,
                        "subscription_status": subscription.status.value,
                        "provider_subscription_id": provider_subscription_id,
                        "source_page": source_page,
                        "scenario_slug": scenario_slug,
                        "paywall_variant": paywall_variant,
                        "pricing_variant": pricing_variant,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="subscription_start",
                    event_id=f"stripe_subscription_started:{provider_subscription_id}",
                )
            elif (
                existing_subscription is not None
                and subscription.status in {SubscriptionStatus.active, SubscriptionStatus.trialing}
                and previous_period_end is not None
                and subscription.current_period_end is not None
                and subscription.current_period_end > previous_period_end
            ):
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.subscription_renewed,
                    user_id=user_id,
                    metadata={
                        "provider": BillingProvider.stripe.value,
                        "plan_tier": plan.tier.value,
                        "subscription_status": subscription.status.value,
                        "provider_subscription_id": provider_subscription_id,
                        "source_page": source_page,
                        "scenario_slug": scenario_slug,
                        "paywall_variant": paywall_variant,
                        "pricing_variant": pricing_variant,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="subscription_renewal",
                    event_id=f"stripe_subscription_renewed:{provider_subscription_id}:{subscription.current_period_end.isoformat()}",
                )

            if subscription.status == SubscriptionStatus.canceled or subscription.canceled_at is not None:
                canceled_marker = subscription.canceled_at.isoformat() if subscription.canceled_at else "none"
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.subscription_canceled,
                    user_id=user_id,
                    metadata={
                        "provider": BillingProvider.stripe.value,
                        "plan_tier": plan.tier.value,
                        "subscription_status": subscription.status.value,
                        "provider_subscription_id": provider_subscription_id,
                        "source_page": source_page,
                        "scenario_slug": scenario_slug,
                        "paywall_variant": paywall_variant,
                        "pricing_variant": pricing_variant,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="subscription_cancel",
                    event_id=f"stripe_subscription_canceled:{provider_subscription_id}:{canceled_marker}",
                )
