from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

from app.core.errors import AppError
from app.infrastructure.db.models import BillingProvider, Plan, PlanTier, SubscriptionStatus, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.billing.model.billing import (
    BillingPortalRequest,
    BillingPortalResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
)
from app.modules.billing.service.billing_stripe_client import stripe
from app.modules.billing.service.billing_utils import append_query


class BillingCheckoutMixin:
    async def _get_or_create_stripe_customer(self, user: User) -> str:
        existing = await self._repo.get_billing_customer_for_user(user.id, provider=BillingProvider.stripe)
        if existing is not None:
            return existing.provider_customer_id

        if not stripe:
            raise AppError(
                code="billing_not_configured",
                status_code=501,
                message="Billing is currently unavailable.",
                message_key="errors.billing_not_configured",
            )

        stripe.api_key = self._settings.stripe_secret_key
        customer = stripe.Customer.create(
            email=user.email,
            name=user.display_name,
            metadata={"user_id": str(user.id)},
        )
        customer_id = str(getattr(customer, "id", None) or customer.get("id"))
        await self._repo.create_billing_customer(
            user_id=user.id,
            provider=BillingProvider.stripe,
            provider_customer_id=customer_id,
            email=user.email,
        )
        return customer_id

    def _ensure_success_url(self, base_url: str) -> str:
        if "{CHECKOUT_SESSION_ID}" in base_url:
            return base_url
        return append_query(base_url, session_id="{CHECKOUT_SESSION_ID}")

    def _redirect_origin(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if not parsed.hostname or parsed.username or parsed.password:
            return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme.lower() == "https" else 80
        return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}:{port}"

    def _allowed_redirect_origins(self) -> set[str]:
        urls = list(self._settings.cors_origin_list)
        urls.extend(
            [
                self._settings.billing_checkout_success_url,
                self._settings.billing_checkout_cancel_url,
                self._settings.billing_portal_return_url,
            ]
        )
        origins: set[str] = set()
        for url in urls:
            origin = self._redirect_origin(url)
            if origin:
                origins.add(origin)
        return origins

    def _resolve_redirect_url(self, candidate: str | None, *, default_url: str) -> str:
        raw = (candidate or "").strip()
        if not raw:
            return default_url

        parsed = urlparse(raw)
        if not parsed.scheme and not parsed.netloc:
            if not raw.startswith("/") or raw.startswith("//"):
                raise AppError(
                    code="invalid_redirect_url",
                    status_code=400,
                    message="This redirect URL is not allowed.",
                )
            raw = urljoin(default_url, raw)

        origin = self._redirect_origin(raw)
        if origin is None or origin not in self._allowed_redirect_origins():
            raise AppError(
                code="invalid_redirect_url",
                status_code=400,
                message="This redirect URL is not allowed.",
            )
        return raw

    async def _create_mock_checkout_session(
        self,
        *,
        user: User,
        plan: Plan,
        payload: CheckoutSessionRequest,
    ) -> CheckoutSessionResponse:
        customer = await self._repo.get_billing_customer_for_user(user.id, provider=BillingProvider.mock)
        if customer is None:
            await self._repo.create_billing_customer(
                user_id=user.id,
                provider=BillingProvider.mock,
                provider_customer_id=f"mock_cus_{uuid.uuid4().hex}",
                email=user.email,
            )

        now = datetime.now(timezone.utc)
        provider_subscription_id = f"mock_sub_{uuid.uuid4().hex}"
        subscription = await self._repo.upsert_subscription(
            user_id=user.id,
            plan_id=plan.id,
            provider=BillingProvider.mock,
            provider_subscription_id=provider_subscription_id,
            status=SubscriptionStatus.active,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            trial_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            metadata_json={"mode": "mock", "tier": plan.tier.value},
        )
        event_id = f"mock_evt_{uuid.uuid4().hex}"
        await self._repo.create_subscription_event(
            subscription_id=subscription.id,
            user_id=user.id,
            provider=BillingProvider.mock,
            provider_event_id=event_id,
            event_type="mock.checkout.completed",
            payload={"tier": plan.tier.value, "provider_subscription_id": provider_subscription_id},
            occurred_at=now,
        )
        await self._entitlements.recalculate_user_tier(user.id)
        if self._analytics is not None:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.subscription_activated,
                user_id=user.id,
                metadata={
                    "provider": BillingProvider.mock.value,
                    "plan_tier": plan.tier.value,
                    "subscription_status": SubscriptionStatus.active.value,
                },
                context_page="/api/v1/billing/checkout/session",
                context_feature="mock_checkout",
                event_id=f"mock_subscription_activated:{provider_subscription_id}",
            )

        success_url = self._resolve_redirect_url(
            payload.success_url,
            default_url=self._settings.billing_checkout_success_url,
        )
        return CheckoutSessionResponse(
            url=append_query(success_url, billing="success", tier=plan.tier.value, mock="1"),
            session_id=provider_subscription_id,
        )

    async def create_checkout_session(
        self,
        *,
        user: User,
        payload: CheckoutSessionRequest,
    ) -> CheckoutSessionResponse:
        plan = await self._repo.get_plan_by_tier(payload.tier)
        if plan is None or not plan.is_active:
            raise AppError(
                code="plan_not_available",
                status_code=404,
                message="This plan is currently unavailable.",
                message_key="errors.plan_not_available",
            )
        if plan.tier == PlanTier.free:
            raise AppError(
                code="invalid_plan",
                status_code=400,
                message="This plan can't be started from checkout.",
                message_key="errors.invalid_plan_for_checkout",
            )

        if self._stripe_checkout_enabled_for_plan(plan):
            assert stripe is not None
            stripe.api_key = self._settings.stripe_secret_key
            customer_id = await self._get_or_create_stripe_customer(user)
            price_id = self._resolve_price_id(plan)
            if price_id is None:
                raise AppError(
                    code="checkout_not_configured",
                    status_code=501,
                    message="Checkout is currently unavailable for this plan.",
                    message_key="errors.checkout_not_configured",
                )
            success_url = self._ensure_success_url(
                self._resolve_redirect_url(
                    payload.success_url,
                    default_url=self._settings.billing_checkout_success_url,
                )
            )
            cancel_url = self._resolve_redirect_url(
                payload.cancel_url,
                default_url=self._settings.billing_checkout_cancel_url,
            )
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer=customer_id,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user.id),
                allow_promotion_codes=True,
                metadata={"user_id": str(user.id), "tier": plan.tier.value},
            )
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.checkout_started,
                    user_id=user.id,
                    metadata={
                        "provider": BillingProvider.stripe.value,
                        "plan_tier": plan.tier.value,
                        "checkout_mode": "subscription",
                    },
                    context_page="/api/v1/billing/checkout/session",
                    context_feature="checkout",
                    event_id=f"stripe_checkout_started:{user.id}:{plan.tier.value}:{getattr(session, 'id', None) or session.get('id')}",
                )
            return CheckoutSessionResponse(
                url=str(getattr(session, "url", None) or session.get("url")),
                session_id=str(getattr(session, "id", None) or session.get("id")),
            )

        if self._settings.billing_mock_mode:
            return await self._create_mock_checkout_session(user=user, plan=plan, payload=payload)

        raise AppError(
            code="checkout_not_configured",
            status_code=501,
            message="Checkout is currently unavailable for this plan.",
            message_key="errors.checkout_not_configured",
        )

    async def create_portal_session(
        self,
        *,
        user: User,
        payload: BillingPortalRequest,
    ) -> BillingPortalResponse:
        if stripe and self._settings.stripe_secret_key:
            stripe.api_key = self._settings.stripe_secret_key
            customer = await self._repo.get_billing_customer_for_user(user.id, provider=BillingProvider.stripe)
            if customer is None:
                raise AppError(
                    code="billing_customer_not_found",
                    status_code=404,
                    message="We couldn't find your billing profile.",
                    message_key="errors.billing_customer_not_found",
                )
            session = stripe.billing_portal.Session.create(
                customer=customer.provider_customer_id,
                return_url=self._resolve_redirect_url(
                    payload.return_url,
                    default_url=self._settings.billing_portal_return_url,
                ),
            )
            return BillingPortalResponse(url=str(getattr(session, "url", None) or session.get("url")))

        if self._settings.billing_mock_mode:
            return BillingPortalResponse(
                url=self._resolve_redirect_url(
                    payload.return_url,
                    default_url=self._settings.billing_portal_return_url,
                )
            )

        raise AppError(
            code="billing_not_configured",
            status_code=501,
            message="Billing settings are currently unavailable.",
            message_key="errors.billing_not_configured",
        )
