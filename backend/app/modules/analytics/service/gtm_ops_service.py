from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from app.core.errors import AppError
from app.infrastructure.db.models import ChannelSpendEntry, SubscriptionStatus, User, UserRole
from app.modules.analytics.model.analytics import AnalyticsAttribution, AnalyticsEventName
from app.modules.analytics.model.gtm import (
    ChannelSpendUpsertRead,
    ChannelSpendUpsertWrite,
    GtmChannelPerformanceRead,
    GtmCreativePerformanceRead,
    GtmDashboardRead,
    GtmHeadlineRead,
    GtmScaleSignalRead,
    GtmSourceFunnelRead,
)
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.repository.billing_repository import BillingRepository

_PAID_EVENT_NAMES = {
    AnalyticsEventName.checkout_completed.value,
    AnalyticsEventName.subscription_started.value,
    AnalyticsEventName.subscription_activated.value,
    AnalyticsEventName.subscription_renewed.value,
}
_ACTIVATION_EVENT_NAMES = {
    AnalyticsEventName.scenario_run.value,
    AnalyticsEventName.onboarding_first_action.value,
}
_SIGNUP_EVENT_NAMES = {
    AnalyticsEventName.signup_completed.value,
    AnalyticsEventName.signup_from_source.value,
}
_TRAFFIC_EVENT_NAMES = {
    AnalyticsEventName.landing_view.value,
    AnalyticsEventName.ad_click.value,
}
_ACTIVE_SUB_STATUSES = (SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due)


@dataclass(slots=True)
class _ChannelAccumulator:
    traffic_sessions: set[str]
    ad_click_sessions: set[str]
    landing_sessions: set[str]
    signups: set[str]
    activated_users: set[str]
    paid_users: set[str]
    revenue_usd: float
    spend_usd: float


@dataclass(slots=True)
class _CreativeAccumulator:
    clicks: int
    signups: set[str]
    activated_users: set[str]
    paid_users: set[str]
    revenue_usd: float


class GtmOpsService:
    def __init__(
        self,
        *,
        analytics_repo: AnalyticsRepository,
        billing_repo: BillingRepository,
        analytics: AnalyticsService,
    ) -> None:
        self._analytics_repo = analytics_repo
        self._billing_repo = billing_repo
        self._analytics = analytics

    def _percent(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)

    def _safe_source(self, value: str | None) -> str:
        normalized = (value or "").strip().lower()
        return normalized or "direct"

    def _safe_medium(self, value: str | None) -> str:
        normalized = (value or "").strip().lower()
        return normalized or "organic"

    def _safe_campaign(self, value: str | None) -> str | None:
        normalized = (value or "").strip().lower()
        return normalized or None

    def _channel_key(self, *, source: str | None, campaign: str | None) -> tuple[str, str | None]:
        return self._safe_source(source), self._safe_campaign(campaign)

    def _spend_dedupe_key(self, payload: ChannelSpendUpsertWrite) -> str:
        if payload.dedupe_key:
            return payload.dedupe_key.strip().lower()
        return (
            f"{payload.spend_day.isoformat()}:"
            f"{(payload.source or '').strip().lower()}:"
            f"{(payload.medium or '').strip().lower()}:"
            f"{(payload.campaign or '').strip().lower()}:"
            f"{(payload.ad_id or '').strip().lower()}:"
            f"{(payload.creative_id or '').strip().lower()}"
        )

    async def upsert_spend(
        self,
        *,
        user: User | None,
        payload: ChannelSpendUpsertWrite,
    ) -> ChannelSpendUpsertRead:
        if user is None or user.role != UserRole.admin:
            raise AppError(
                code="insufficient_permissions",
                message="You don't have access to this action.",
                status_code=403,
                message_key="errors.insufficient_permissions",
            )

        dedupe_key = self._spend_dedupe_key(payload)
        now = datetime.now(timezone.utc)
        row = await self._analytics_repo.get_channel_spend_by_dedupe_key(dedupe_key=dedupe_key)
        if row is None:
            row = ChannelSpendEntry(
                spend_day=payload.spend_day,
                source=self._safe_source(payload.source),
                medium=self._safe_medium(payload.medium),
                campaign=self._safe_campaign(payload.campaign),
                ad_id=(payload.ad_id or "").strip().lower() or None,
                creative_id=(payload.creative_id or "").strip().lower() or None,
                cost_usd_cents=int(round(payload.cost_usd * 100)),
                clicks=int(payload.clicks),
                impressions=int(payload.impressions),
                dedupe_key=dedupe_key,
                created_at=now,
                updated_at=now,
            )
            row = await self._analytics_repo.create_channel_spend(row)
        else:
            row.spend_day = payload.spend_day
            row.source = self._safe_source(payload.source)
            row.medium = self._safe_medium(payload.medium)
            row.campaign = self._safe_campaign(payload.campaign)
            row.ad_id = (payload.ad_id or "").strip().lower() or None
            row.creative_id = (payload.creative_id or "").strip().lower() or None
            row.cost_usd_cents = int(round(payload.cost_usd * 100))
            row.clicks = int(payload.clicks)
            row.impressions = int(payload.impressions)
            row.updated_at = now
            row = await self._analytics_repo.save_channel_spend(row)

        return ChannelSpendUpsertRead(
            id=str(row.id),
            spend_day=row.spend_day,
            source=row.source,
            medium=row.medium,
            campaign=row.campaign,
            ad_id=row.ad_id,
            creative_id=row.creative_id,
            cost_usd=round(row.cost_usd_cents / 100.0, 2),
            clicks=row.clicks,
            impressions=row.impressions,
            dedupe_key=row.dedupe_key,
            updated_at=row.updated_at,
        )

    async def dashboard(
        self,
        *,
        user: User | None,
        window_days: int,
    ) -> GtmDashboardRead:
        if user is None or user.role != UserRole.admin:
            raise AppError(
                code="insufficient_permissions",
                message="You don't have access to this action.",
                status_code=403,
                message_key="errors.insufficient_permissions",
            )

        now = datetime.now(timezone.utc)
        window_days = max(7, min(90, int(window_days)))
        from_ts = now - timedelta(days=window_days)
        rows = await self._analytics_repo.list_event_rows_with_dims(
            from_ts=from_ts,
            to_ts=now,
            event_names=sorted(
                {
                    *_TRAFFIC_EVENT_NAMES,
                    *_SIGNUP_EVENT_NAMES,
                    *_ACTIVATION_EVENT_NAMES,
                    *_PAID_EVENT_NAMES,
                }
            ),
        )
        subscriptions = await self._billing_repo.list_subscriptions()
        spend_rows = await self._analytics_repo.list_channel_spend_rows(
            day_from=from_ts.date(),
            day_to=now.date(),
        )

        user_ids = {
            str(user_id) for user_id, _session, _event, _at, _meta, _utm_source, _utm_medium, _utm_campaign, _ad_id, _creative_id in rows if user_id is not None
        }
        user_ids.update(str(sub.user_id) for sub in subscriptions)
        attributions = await self._analytics_repo.list_user_attributions(
            user_ids=[uuid.UUID(raw) for raw in user_ids] if user_ids else []
        )
        attribution_by_user = {str(row.user_id): row for row in attributions}

        channel_acc: dict[tuple[str, str | None], _ChannelAccumulator] = {}
        creative_acc: dict[tuple[str, str | None, str | None, str | None], _CreativeAccumulator] = {}
        source_funnel_sessions: dict[str, set[str]] = defaultdict(set)
        source_funnel_signups: dict[str, set[str]] = defaultdict(set)
        source_funnel_activated: dict[str, set[str]] = defaultdict(set)
        source_funnel_paid: dict[str, set[str]] = defaultdict(set)

        def ensure_channel(key: tuple[str, str | None]) -> _ChannelAccumulator:
            existing = channel_acc.get(key)
            if existing is not None:
                return existing
            created = _ChannelAccumulator(
                traffic_sessions=set(),
                ad_click_sessions=set(),
                landing_sessions=set(),
                signups=set(),
                activated_users=set(),
                paid_users=set(),
                revenue_usd=0.0,
                spend_usd=0.0,
            )
            channel_acc[key] = created
            return created

        def ensure_creative(key: tuple[str, str | None, str | None, str | None]) -> _CreativeAccumulator:
            existing = creative_acc.get(key)
            if existing is not None:
                return existing
            created = _CreativeAccumulator(
                clicks=0,
                signups=set(),
                activated_users=set(),
                paid_users=set(),
                revenue_usd=0.0,
            )
            creative_acc[key] = created
            return created

        for user_id, session_id, event_name, _occurred_at, metadata, utm_source, _utm_medium, utm_campaign, ad_id, creative_id in rows:
            source = self._safe_source(utm_source or str(metadata.get("source") or ""))
            campaign = self._safe_campaign(utm_campaign or str(metadata.get("campaign") or ""))
            channel_key = self._channel_key(source=source, campaign=campaign)
            channel = ensure_channel(channel_key)

            if event_name in _TRAFFIC_EVENT_NAMES:
                channel.traffic_sessions.add(session_id)
                source_funnel_sessions[source].add(session_id)
                if event_name == AnalyticsEventName.ad_click.value:
                    channel.ad_click_sessions.add(session_id)
                    creative_key = (
                        source,
                        campaign,
                        (ad_id or str(metadata.get("ad_id") or "")).strip().lower() or None,
                        (creative_id or str(metadata.get("creative_id") or "")).strip().lower() or None,
                    )
                    ensure_creative(creative_key).clicks += 1
                if event_name == AnalyticsEventName.landing_view.value:
                    channel.landing_sessions.add(session_id)

            if user_id is None:
                continue
            user_key = str(user_id)
            user_attr = attribution_by_user.get(user_key)
            if user_attr is not None:
                source = self._safe_source(user_attr.first_utm_source or source)
                campaign = self._safe_campaign(user_attr.first_utm_campaign or campaign)
                channel_key = self._channel_key(source=source, campaign=campaign)
                channel = ensure_channel(channel_key)
                creative_key = (
                    source,
                    campaign,
                    self._safe_campaign(user_attr.first_ad_id),
                    self._safe_campaign(user_attr.first_creative_id),
                )
                creative = ensure_creative(creative_key)
            else:
                creative = ensure_creative(
                    (
                        source,
                        campaign,
                        (ad_id or str(metadata.get("ad_id") or "")).strip().lower() or None,
                        (creative_id or str(metadata.get("creative_id") or "")).strip().lower() or None,
                    )
                )

            if event_name in _SIGNUP_EVENT_NAMES:
                channel.signups.add(user_key)
                source_funnel_signups[source].add(user_key)
                creative.signups.add(user_key)
            if event_name in _ACTIVATION_EVENT_NAMES:
                channel.activated_users.add(user_key)
                source_funnel_activated[source].add(user_key)
                creative.activated_users.add(user_key)
            if event_name in _PAID_EVENT_NAMES:
                channel.paid_users.add(user_key)
                source_funnel_paid[source].add(user_key)
                creative.paid_users.add(user_key)

        active_subscriptions = [sub for sub in subscriptions if sub.status in _ACTIVE_SUB_STATUSES and sub.plan is not None]
        for sub in active_subscriptions:
            user_key = str(sub.user_id)
            user_attr = attribution_by_user.get(user_key)
            source = self._safe_source(user_attr.first_utm_source if user_attr else None)
            campaign = self._safe_campaign(user_attr.first_utm_campaign if user_attr else None)
            revenue = float(sub.plan.price_usd_month)

            channel = ensure_channel((source, campaign))
            channel.paid_users.add(user_key)
            channel.revenue_usd += revenue

            creative_key = (
                source,
                campaign,
                self._safe_campaign(user_attr.first_ad_id if user_attr else None),
                self._safe_campaign(user_attr.first_creative_id if user_attr else None),
            )
            creative = ensure_creative(creative_key)
            creative.paid_users.add(user_key)
            creative.revenue_usd += revenue

        for spend in spend_rows:
            channel = ensure_channel((self._safe_source(spend.source), self._safe_campaign(spend.campaign)))
            channel.spend_usd += float(spend.cost_usd_cents) / 100.0
            if spend.ad_id or spend.creative_id:
                creative = ensure_creative(
                    (
                        self._safe_source(spend.source),
                        self._safe_campaign(spend.campaign),
                        self._safe_campaign(spend.ad_id),
                        self._safe_campaign(spend.creative_id),
                    )
                )
                creative.clicks += max(spend.clicks, 0)

        channel_rows: list[GtmChannelPerformanceRead] = []
        for (source, campaign), acc in channel_acc.items():
            traffic = len(acc.traffic_sessions)
            signups = len(acc.signups)
            activated = len(acc.activated_users)
            paid = len(acc.paid_users)
            revenue = round(acc.revenue_usd, 2)
            spend = round(acc.spend_usd, 2)
            cac = round(spend / paid, 2) if spend > 0 and paid > 0 else None
            roi = round(((revenue - spend) / spend) * 100.0, 2) if spend > 0 else None
            arppu = round(revenue / paid, 2) if paid > 0 else None
            ltv_cac = round(arppu / cac, 2) if arppu is not None and cac is not None and cac > 0 else None
            channel_rows.append(
                GtmChannelPerformanceRead(
                    source=source,
                    campaign=campaign,
                    traffic_sessions=traffic,
                    ad_clicks=len(acc.ad_click_sessions),
                    landing_views=len(acc.landing_sessions),
                    signups=signups,
                    activated_users=activated,
                    paid_users=paid,
                    revenue_usd=revenue,
                    spend_usd=spend,
                    signup_rate=self._percent(signups, max(traffic, len(acc.landing_sessions))),
                    activation_rate=self._percent(activated, max(signups, 1)),
                    conversion_rate=self._percent(paid, max(activated, 1)),
                    cac_usd=cac,
                    roi_percent=roi,
                    ltv_cac_proxy=ltv_cac,
                )
            )

        channel_rows.sort(key=lambda item: (item.source, item.campaign or "", -item.revenue_usd))
        top_campaigns = sorted(
            [row for row in channel_rows if row.campaign],
            key=lambda item: (item.revenue_usd, item.conversion_rate),
            reverse=True,
        )[:12]

        creative_rows: list[GtmCreativePerformanceRead] = []
        for (source, campaign, ad_id_value, creative_id_value), acc in creative_acc.items():
            if not (ad_id_value or creative_id_value):
                continue
            paid = len(acc.paid_users)
            activated = len(acc.activated_users)
            creative_rows.append(
                GtmCreativePerformanceRead(
                    source=source,
                    campaign=campaign,
                    ad_id=ad_id_value,
                    creative_id=creative_id_value,
                    clicks=acc.clicks,
                    signups=len(acc.signups),
                    activated_users=activated,
                    paid_users=paid,
                    revenue_usd=round(acc.revenue_usd, 2),
                    conversion_rate=self._percent(paid, max(activated, 1)),
                )
            )
        creative_rows.sort(key=lambda item: (item.revenue_usd, item.conversion_rate), reverse=True)
        top_creatives = creative_rows[:20]

        funnel_rows: list[GtmSourceFunnelRead] = []
        sources = sorted(
            set(source_funnel_sessions.keys())
            | set(source_funnel_signups.keys())
            | set(source_funnel_activated.keys())
            | set(source_funnel_paid.keys())
        )
        for source in sources:
            acquired = len(source_funnel_sessions[source])
            signed_up = len(source_funnel_signups[source])
            activated = len(source_funnel_activated[source])
            paid = len(source_funnel_paid[source])
            funnel_rows.append(
                GtmSourceFunnelRead(
                    source=source,
                    acquired=acquired,
                    signed_up=signed_up,
                    activated=activated,
                    paid=paid,
                    acquired_to_signup=self._percent(signed_up, max(acquired, 1)),
                    signup_to_activated=self._percent(activated, max(signed_up, 1)),
                    activated_to_paid=self._percent(paid, max(activated, 1)),
                )
            )
        funnel_rows.sort(key=lambda item: item.source)

        signals = await self._signals(now=now, rows=channel_rows)

        total_traffic = len({session for row in channel_acc.values() for session in row.traffic_sessions})
        total_signups = len({user_key for row in channel_acc.values() for user_key in row.signups})
        total_activated = len({user_key for row in channel_acc.values() for user_key in row.activated_users})
        total_paid = len({user_key for row in channel_acc.values() for user_key in row.paid_users})
        total_revenue = round(sum(row.revenue_usd for row in channel_rows), 2)
        total_spend = round(sum(row.spend_usd for row in channel_rows), 2)
        blended_cac = round(total_spend / total_paid, 2) if total_spend > 0 and total_paid > 0 else None
        blended_roi = round(((total_revenue - total_spend) / total_spend) * 100.0, 2) if total_spend > 0 else None

        return GtmDashboardRead(
            headline=GtmHeadlineRead(
                window_days=window_days,
                computed_at=now,
                traffic_sessions=total_traffic,
                signups=total_signups,
                activated_users=total_activated,
                paid_users=total_paid,
                revenue_usd=total_revenue,
                spend_usd=total_spend,
                blended_cac_usd=blended_cac,
                blended_roi_percent=blended_roi,
            ),
            channels=channel_rows,
            funnel_by_source=funnel_rows,
            top_campaigns=top_campaigns,
            top_creatives=top_creatives,
            signals=signals,
        )

    async def _signals(self, *, now: datetime, rows: list[GtmChannelPerformanceRead]) -> list[GtmScaleSignalRead]:
        signals: list[GtmScaleSignalRead] = []
        for row in rows:
            if row.spend_usd < 100:
                continue
            signal: str | None = None
            reason: str | None = None
            if row.roi_percent is not None and row.roi_percent >= 30.0 and row.conversion_rate >= 5.0 and row.paid_users >= 2:
                signal = AnalyticsEventName.scale_channel.value
                reason = "high_roi_and_conversion"
            elif (row.roi_percent is not None and row.roi_percent < 0) or row.conversion_rate < 1.0:
                signal = AnalyticsEventName.kill_channel.value
                reason = "negative_roi_or_low_conversion"
            if signal is None or reason is None:
                continue

            read_row = GtmScaleSignalRead(
                signal="scale_channel" if signal == AnalyticsEventName.scale_channel.value else "kill_channel",
                source=row.source,
                campaign=row.campaign,
                reason=reason,
                roi_percent=row.roi_percent,
                cac_usd=row.cac_usd,
                conversion_rate=row.conversion_rate,
            )
            signals.append(read_row)

            await self._analytics.record_server_event(
                event_name=AnalyticsEventName(signal),
                user_id=None,
                event_id=f"{signal}:{row.source}:{row.campaign or 'all'}:{now.date().isoformat()}",
                metadata={
                    "source": row.source,
                    "campaign": row.campaign,
                    "reason": reason,
                    "roi_percent": row.roi_percent,
                    "cac_usd": row.cac_usd,
                    "conversion_rate": row.conversion_rate,
                },
                attribution=AnalyticsAttribution(
                    utm_source=row.source,
                    utm_campaign=row.campaign,
                ),
                context_page="/api/v1/analytics/gtm/dashboard",
                context_feature="channel_scaling_signal",
            )
        return signals

