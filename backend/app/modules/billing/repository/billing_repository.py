import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    BillingCustomer,
    BillingProvider,
    Plan,
    PlanTier,
    ProcessedWebhookEvent,
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
)


class BillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_plans(self) -> Sequence[Plan]:
        stmt = select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order, Plan.price_usd_month)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_plan_by_tier(self, tier: PlanTier) -> Plan | None:
        result = await self._session.execute(select(Plan).where(Plan.tier == tier))
        return result.scalar_one_or_none()

    async def get_plan_by_stripe_price_id(self, stripe_price_id: str) -> Plan | None:
        result = await self._session.execute(select(Plan).where(Plan.stripe_price_id == stripe_price_id))
        return result.scalar_one_or_none()

    async def get_billing_customer_for_user(
        self,
        user_id: uuid.UUID,
        *,
        provider: BillingProvider | None = None,
    ) -> BillingCustomer | None:
        stmt: Select[tuple[BillingCustomer]] = select(BillingCustomer).where(BillingCustomer.user_id == user_id)
        if provider is not None:
            stmt = stmt.where(BillingCustomer.provider == provider)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_billing_customer_by_provider_customer_id(
        self,
        provider: BillingProvider,
        provider_customer_id: str,
    ) -> BillingCustomer | None:
        result = await self._session.execute(
            select(BillingCustomer).where(
                BillingCustomer.provider == provider,
                BillingCustomer.provider_customer_id == provider_customer_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_billing_customer(
        self,
        *,
        user_id: uuid.UUID,
        provider: BillingProvider,
        provider_customer_id: str,
        email: str | None,
    ) -> BillingCustomer:
        customer = BillingCustomer(
            user_id=user_id,
            provider=provider,
            provider_customer_id=provider_customer_id,
            email=email,
        )
        self._session.add(customer)
        await self._session.flush()
        await self._session.refresh(customer)
        return customer

    async def has_billing_customer(self, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(BillingCustomer.id).where(BillingCustomer.user_id == user_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_subscription_by_provider_subscription_id(
        self,
        provider: BillingProvider,
        provider_subscription_id: str,
    ) -> Subscription | None:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.provider == provider,
                Subscription.provider_subscription_id == provider_subscription_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_subscription(
        self,
        *,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        provider: BillingProvider,
        provider_subscription_id: str,
        status: SubscriptionStatus,
        current_period_start: datetime | None,
        current_period_end: datetime | None,
        trial_end: datetime | None,
        cancel_at_period_end: bool,
        canceled_at: datetime | None,
        metadata_json: dict | None,
    ) -> Subscription:
        subscription = await self.get_subscription_by_provider_subscription_id(
            provider,
            provider_subscription_id,
        )
        if subscription is None:
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                provider=provider,
                provider_subscription_id=provider_subscription_id,
                status=status,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                trial_end=trial_end,
                cancel_at_period_end=cancel_at_period_end,
                canceled_at=canceled_at,
                metadata_json=metadata_json,
            )
            self._session.add(subscription)
        else:
            subscription.user_id = user_id
            subscription.plan_id = plan_id
            subscription.status = status
            subscription.current_period_start = current_period_start
            subscription.current_period_end = current_period_end
            subscription.trial_end = trial_end
            subscription.cancel_at_period_end = cancel_at_period_end
            subscription.canceled_at = canceled_at
            subscription.metadata_json = metadata_json

        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription

    async def get_latest_subscription_for_user(self, user_id: uuid.UUID) -> Subscription | None:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.updated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_entitled_subscriptions_for_user(
        self,
        user_id: uuid.UUID,
        *,
        statuses: Sequence[SubscriptionStatus],
    ) -> Sequence[Subscription]:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(list(statuses)),
            )
            .order_by(Subscription.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_subscriptions(
        self,
        *,
        statuses: Sequence[SubscriptionStatus] | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> Sequence[Subscription]:
        stmt = select(Subscription).options(selectinload(Subscription.plan))
        if statuses:
            stmt = stmt.where(Subscription.status.in_(list(statuses)))
        if from_ts is not None:
            stmt = stmt.where(Subscription.created_at >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(Subscription.created_at < to_ts)
        stmt = stmt.order_by(Subscription.created_at.asc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_subscription_event(
        self,
        *,
        subscription_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        provider: BillingProvider,
        provider_event_id: str,
        event_type: str,
        payload: dict,
        occurred_at: datetime | None,
    ) -> SubscriptionEvent:
        event = SubscriptionEvent(
            subscription_id=subscription_id,
            user_id=user_id,
            provider=provider,
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
            occurred_at=occurred_at,
        )
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def list_subscription_events(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        event_types: Sequence[str] | None = None,
    ) -> Sequence[SubscriptionEvent]:
        stmt = select(SubscriptionEvent).order_by(SubscriptionEvent.created_at.asc())
        if from_ts is not None:
            stmt = stmt.where(SubscriptionEvent.created_at >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(SubscriptionEvent.created_at < to_ts)
        if event_types:
            stmt = stmt.where(SubscriptionEvent.event_type.in_(list(event_types)))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def has_processed_webhook_event(self, *, provider: BillingProvider, event_id: str) -> bool:
        result = await self._session.execute(
            select(ProcessedWebhookEvent.id).where(
                ProcessedWebhookEvent.provider == provider,
                ProcessedWebhookEvent.event_id == event_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def try_claim_webhook_event(
        self,
        *,
        provider: BillingProvider,
        event_id: str,
        payload_hash: str | None,
    ) -> uuid.UUID | None:
        """Insert idempotency row before processing. Returns claim id, or None if duplicate."""
        claim_id = uuid.uuid4()
        marker = ProcessedWebhookEvent(
            id=claim_id,
            provider=provider,
            event_id=event_id,
            payload_hash=payload_hash,
        )
        try:
            async with self._session.begin_nested():
                self._session.add(marker)
                await self._session.flush()
        except IntegrityError:
            return None
        return claim_id

    async def delete_webhook_claim(self, *, claim_id: uuid.UUID) -> None:
        await self._session.execute(delete(ProcessedWebhookEvent).where(ProcessedWebhookEvent.id == claim_id))
        await self._session.flush()

    async def mark_webhook_processed(
        self,
        *,
        provider: BillingProvider,
        event_id: str,
        payload_hash: str | None,
    ) -> bool:
        if await self.has_processed_webhook_event(provider=provider, event_id=event_id):
            return False
        marker = ProcessedWebhookEvent(
            provider=provider,
            event_id=event_id,
            payload_hash=payload_hash,
        )
        self._session.add(marker)
        await self._session.flush()
        return True
