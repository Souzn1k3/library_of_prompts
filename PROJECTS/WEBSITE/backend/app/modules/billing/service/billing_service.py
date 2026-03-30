import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from app.config import Settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.infrastructure.db.models import (
    BillingProvider,
    Plan,
    PlanTier,
    SubscriptionStatus,
    User,
)
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.model.billing import (
    BillingPortalRequest,
    BillingPortalResponse,
    BillingStatusRead,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PlanPublicRead,
)
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.billing.service.entitlement_service import EntitlementService
from app.modules.identity.repository.user_repository import UserRepository

try:
    import stripe
except Exception:  # pragma: no cover - optional runtime dependency
    stripe = None

log = get_logger(__name__)


def _to_datetime_from_unix(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def _append_query(url: str, **params: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({k: v for k, v in params.items() if v})
    encoded = urlencode(query)
    return urlunparse(parsed._replace(query=encoded))


def _safe_uuid(value: Any) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


class BillingService:
    _PLAN_COPY: dict[str, dict[PlanTier, dict[str, object]]] = {
        "en": {
            PlanTier.free: {
                "name": "Free",
                "features": ["Browse catalog", "Save prompts", "Community submissions"],
            },
            PlanTier.starter: {
                "name": "Starter",
                "features": ["Premium prompt bodies", "Email support"],
            },
            PlanTier.pro: {
                "name": "Pro",
                "features": ["Restricted categories", "Full lesson library", "Priority moderation"],
            },
            PlanTier.enterprise: {
                "name": "MAX",
                "features": ["Team seats", "SSO (roadmap)", "Custom agreements"],
            },
        },
        "ru": {
            PlanTier.free: {
                "name": "Free",
                "features": ["Просмотр каталога", "Сохранение промптов", "Публикации сообщества"],
            },
            PlanTier.starter: {
                "name": "Starter",
                "features": ["Премиальные тексты промптов", "Поддержка по email"],
            },
            PlanTier.pro: {
                "name": "Pro",
                "features": ["Ограниченные категории", "Полная библиотека уроков", "Приоритетная модерация"],
            },
            PlanTier.enterprise: {
                "name": "MAX",
                "features": ["Командные места", "SSO (в планах)", "Кастомные договоры"],
            },
        },
        "tt": {
            PlanTier.free: {
                "name": "Бушлай",
                "features": ["Каталогны карау", "Промптларны саклау", "Җәмәгать җибәргән материаллар"],
            },
            PlanTier.starter: {
                "name": "Starter",
                "features": ["Премиум промпт текстлары", "Email аша ярдәм"],
            },
            PlanTier.pro: {
                "name": "Pro",
                "features": ["Чикләнгән категорияләр", "Дәресләрнең тулы китапханәсе", "Өстен модерация"],
            },
            PlanTier.enterprise: {
                "name": "MAX",
                "features": ["Команда урыннары", "SSO (планда)", "Махсус килешүләр"],
            },
        },
    }

    def __init__(
        self,
        repo: BillingRepository,
        entitlement_service: EntitlementService,
        user_repo: UserRepository,
        settings: Settings,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._entitlements = entitlement_service
        self._users = user_repo
        self._settings = settings
        self._analytics = analytics

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
            items.append(
                PlanPublicRead(
                    tier=row.tier,
                    name=str(localized.get("name") or row.name),
                    description=row.description,
                    price_usd_month=row.price_usd_month,
                    features=list(localized.get("features") or []),
                    sort_order=row.sort_order,
                    is_active=row.is_active,
                )
            )
        return items

    async def get_subscription_status(self, user: User) -> BillingStatusRead:
        latest = await self._repo.get_latest_subscription_for_user(user.id)
        return BillingStatusRead(
            plan_tier=user.plan_tier,
            subscription_tier=latest.plan.tier if latest and latest.plan else None,
            provider=latest.provider if latest else None,
            status=latest.status if latest else None,
            current_period_end=latest.current_period_end if latest else None,
            cancel_at_period_end=latest.cancel_at_period_end if latest else False,
            updated_at=latest.updated_at if latest else None,
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
        return _append_query(base_url, session_id="{CHECKOUT_SESSION_ID}")

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
            url=_append_query(success_url, billing="success", tier=plan.tier.value, mock="1"),
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
                line_items=[{"price": self._resolve_price_id(plan), "quantity": 1}],
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
            user_id = _safe_uuid(metadata.get("user_id"))
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
            existing_subscription = await self._repo.get_subscription_by_provider_subscription_id(
                BillingProvider.stripe,
                provider_subscription_id,
            )
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
            current_period_start=_to_datetime_from_unix(stripe_subscription.get("current_period_start")),
            current_period_end=_to_datetime_from_unix(stripe_subscription.get("current_period_end")),
            trial_end=_to_datetime_from_unix(stripe_subscription.get("trial_end")),
            cancel_at_period_end=bool(stripe_subscription.get("cancel_at_period_end", False)),
            canceled_at=_to_datetime_from_unix(stripe_subscription.get("canceled_at")),
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

        if self._analytics is not None and subscription.status in {SubscriptionStatus.active, SubscriptionStatus.trialing}:
            period_end_marker = subscription.current_period_end.isoformat() if subscription.current_period_end else "none"
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.subscription_activated,
                user_id=user_id,
                metadata={
                    "provider": BillingProvider.stripe.value,
                    "plan_tier": plan.tier.value,
                    "subscription_status": subscription.status.value,
                    "provider_subscription_id": provider_subscription_id,
                },
                context_page="/api/v1/billing/webhooks",
                context_feature="subscription_sync",
                event_id=f"stripe_subscription_activated:{provider_subscription_id}:{subscription.status.value}:{period_end_marker}",
            )

    async def _process_stripe_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        provider_event_id = str(event.get("id") or f"evt_{uuid.uuid4().hex}")
        occurred_at = _to_datetime_from_unix(event.get("created"))
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
                return
            fallback_user_id = _safe_uuid(obj.get("client_reference_id"))
            if fallback_user_id is None:
                metadata = obj.get("metadata") or {}
                fallback_user_id = _safe_uuid(metadata.get("user_id"))
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
                subscription_payload = (
                    subscription if isinstance(subscription, dict) else subscription.to_dict_recursive()
                )
                await self._sync_subscription_from_stripe(
                    stripe_subscription=subscription_payload,
                    provider_event_id=provider_event_id,
                    event_type=event_type,
                    occurred_at=occurred_at,
                    fallback_user_id=fallback_user_id,
                )

    async def handle_webhook(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
    ) -> dict[str, str]:
        if not self._stripe_webhook_enabled():
            log.warning("billing_webhook_failed", reason="not_configured")
            raise AppError(
                code="billing_not_configured",
                status_code=501,
                message="Payment updates are currently unavailable.",
                message_key="errors.billing_not_configured",
            )
        if not signature_header:
            log.warning(
                "billing_webhook_failed",
                observability_event="billing_webhook_signature_missing",
                reason="missing_signature",
            )
            raise AppError(
                code="invalid_webhook_signature",
                status_code=400,
                message="We couldn't verify this payment update.",
                message_key="errors.invalid_webhook_signature",
            )
        assert stripe is not None
        stripe.api_key = self._settings.stripe_secret_key
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature_header,
                secret=self._settings.stripe_webhook_secret,
            )
        except Exception as exc:
            log.warning(
                "billing_webhook_failed",
                observability_event="billing_webhook_signature_invalid",
                reason="invalid_signature",
                error_type=type(exc).__name__,
            )
            raise AppError(
                code="invalid_webhook_signature",
                status_code=400,
                message="We couldn't verify this payment update.",
                message_key="errors.invalid_webhook_signature",
            ) from exc

        event_dict = event if isinstance(event, dict) else event.to_dict_recursive()
        event_id = str(event_dict.get("id") or "")
        if not event_id:
            log.warning("billing_webhook_failed", reason="missing_event_id")
            raise AppError(
                code="invalid_webhook_payload",
                status_code=400,
                message="We couldn't process this payment update.",
                message_key="errors.invalid_webhook_payload",
            )
        payload_hash = hashlib.sha256(payload).hexdigest()
        claim_id = await self._repo.try_claim_webhook_event(
            provider=BillingProvider.stripe,
            event_id=event_id,
            payload_hash=payload_hash,
        )
        if claim_id is None:
            log.info(
                "billing_webhook_duplicate",
                observability_event="billing_webhook_duplicate",
                stripe_event_id=event_id,
            )
            return {"status": "duplicate"}

        try:
            await self._process_stripe_event(event_dict)
        except Exception:
            await self._repo.delete_webhook_claim(claim_id=claim_id)
            log.exception(
                "billing_webhook_failed",
                observability_event="billing_webhook_processing_error",
                reason="processing_error",
                stripe_event_id=event_id,
                stripe_event_type=str(event_dict.get("type") or ""),
            )
            raise AppError(
                code="webhook_processing_failed",
                status_code=500,
                message="We couldn't complete this payment update.",
            ) from None
        return {"status": "ok"}
