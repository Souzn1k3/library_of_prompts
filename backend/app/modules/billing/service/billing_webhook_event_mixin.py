from __future__ import annotations

import uuid
from typing import Any

from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.billing.service.billing_stripe_client import stripe
from app.modules.billing.service.billing_utils import safe_uuid, stripe_object_to_dict, to_datetime_from_unix


class BillingWebhookEventMixin:
    async def _process_stripe_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        provider_event_id = str(event.get("id") or f"evt_{uuid.uuid4().hex}")
        occurred_at = to_datetime_from_unix(event.get("created"))
        payload = event.get("data") or {}
        obj = payload.get("object") if isinstance(payload, dict) else {}
        if not isinstance(obj, dict):
            return

        if event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            await self._sync_subscription_from_stripe(
                stripe_subscription=obj,
                provider_event_id=provider_event_id,
                event_type=event_type,
                occurred_at=occurred_at,
            )
            return

        if event_type == "checkout.session.completed":
            if obj.get("mode") != "subscription":
                if self._marketplace is not None and (obj.get("metadata") or {}).get("kind") == "prompt_purchase":
                    await self._marketplace.complete_checkout_purchase(
                        checkout_id=str(obj.get("id") or ""),
                        payment_id=str(obj.get("payment_intent") or "") or None,
                        completed_at=occurred_at,
                    )
                return
            fallback_user_id = safe_uuid(obj.get("client_reference_id"))
            if fallback_user_id is None:
                metadata = obj.get("metadata") or {}
                fallback_user_id = safe_uuid(metadata.get("user_id"))
            metadata = obj.get("metadata") or {}
            if self._analytics is not None and fallback_user_id is not None:
                attribution = await self._analytics.get_user_last_touch_attribution(user_id=fallback_user_id)
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.checkout_completed,
                    user_id=fallback_user_id,
                    metadata={
                        "provider": "stripe",
                        "checkout_id": str(obj.get("id") or ""),
                        "subscription_id": str(obj.get("subscription") or ""),
                        "plan_tier": metadata.get("tier"),
                        "source_page": metadata.get("source_page") or None,
                        "scenario_slug": metadata.get("scenario_slug") or None,
                        "paywall_variant": metadata.get("paywall_variant") or None,
                        "pricing_variant": metadata.get("pricing_variant") or None,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="checkout_completed",
                    event_id=f"stripe_checkout_completed:{provider_event_id}",
                )
            provider_customer_id = obj.get("customer")
            if provider_customer_id and fallback_user_id is not None:
                await self._ensure_customer_mapping(
                    user_id=fallback_user_id,
                    provider_customer_id=str(provider_customer_id),
                )
            subscription_id = obj.get("subscription")
            if subscription_id:
                assert stripe is not None
                stripe.api_key = self._settings.stripe_secret_key
                subscription = stripe.Subscription.retrieve(
                    subscription_id,
                    expand=["items.data.price"],
                )
                subscription_payload = stripe_object_to_dict(subscription)
                await self._sync_subscription_from_stripe(
                    stripe_subscription=subscription_payload,
                    provider_event_id=provider_event_id,
                    event_type=event_type,
                    occurred_at=occurred_at,
                    fallback_user_id=fallback_user_id,
                )
            return

        if event_type == "checkout.session.expired":
            if self._marketplace is not None and (obj.get("metadata") or {}).get("kind") == "prompt_purchase":
                await self._marketplace.fail_checkout_purchase(
                    checkout_id=str(obj.get("id") or ""),
                    reason="checkout_expired",
                )
            return

        if event_type == "charge.refunded":
            metadata = obj.get("metadata") or {}
            refund_user_id = safe_uuid(metadata.get("user_id")) if isinstance(metadata, dict) else None
            if self._analytics is not None and refund_user_id is not None:
                attribution = await self._analytics.get_user_last_touch_attribution(user_id=refund_user_id)
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.refund_processed,
                    user_id=refund_user_id,
                    metadata={
                        "provider": "stripe",
                        "payment_intent": str(obj.get("payment_intent") or ""),
                        "reason": obj.get("reason"),
                        "source_page": metadata.get("source_page") if isinstance(metadata, dict) else None,
                        "scenario_slug": metadata.get("scenario_slug") if isinstance(metadata, dict) else None,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="refund",
                    event_id=f"stripe_refund_processed:{provider_event_id}",
                )
            if self._marketplace is not None and (obj.get("metadata") or {}).get("kind") == "prompt_purchase":
                payment_id = str(obj.get("payment_intent") or "")
                if payment_id:
                    await self._marketplace.refund_checkout_purchase(
                        payment_id=payment_id,
                        reason="charge_refunded",
                    )
            return

        if event_type == "payment_intent.payment_failed":
            metadata = obj.get("metadata") or {}
            failed_user_id = safe_uuid(metadata.get("user_id")) if isinstance(metadata, dict) else None
            if self._analytics is not None and failed_user_id is not None:
                attribution = await self._analytics.get_user_last_touch_attribution(user_id=failed_user_id)
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.payment_failed,
                    user_id=failed_user_id,
                    metadata={
                        "provider": "stripe",
                        "payment_intent": str(obj.get("id") or ""),
                        "last_payment_error": str((obj.get("last_payment_error") or {}).get("message") or ""),
                        "source_page": metadata.get("source_page") if isinstance(metadata, dict) else None,
                        "scenario_slug": metadata.get("scenario_slug") if isinstance(metadata, dict) else None,
                        "paywall_variant": metadata.get("paywall_variant") if isinstance(metadata, dict) else None,
                        "pricing_variant": metadata.get("pricing_variant") if isinstance(metadata, dict) else None,
                    },
                    attribution=attribution,
                    context_page="/api/v1/billing/webhooks",
                    context_feature="payment_failed",
                    event_id=f"stripe_payment_failed:{provider_event_id}",
                )
            if self._marketplace is not None and (obj.get("metadata") or {}).get("kind") == "prompt_purchase":
                purchase_id = safe_uuid((obj.get("metadata") or {}).get("purchase_id"))
                if purchase_id is not None:
                    await self._marketplace.fail_checkout_purchase_by_id(
                        purchase_id=purchase_id,
                        reason="payment_failed",
                    )
