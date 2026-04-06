from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import uuid

from app.config import Settings
from app.core.errors import AppError
from app.infrastructure.db.models import PlanTier, SubscriptionStatus, User, UserRole
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.model.revenue import (
    RevenueChurnSignalRead,
    RevenueCohortRead,
    RevenueDashboardRead,
    RevenueExperimentVariantRead,
    RevenueFunnelRead,
    RevenueFunnelStepRead,
    RevenueHeadlineRead,
    RevenueSourceRead,
)
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.repository.billing_repository import BillingRepository

_ACTIVE_SUB_STATUSES = (SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due)
_PAID_EVENT_NAMES = {
    AnalyticsEventName.checkout_completed.value,
    AnalyticsEventName.subscription_started.value,
    AnalyticsEventName.subscription_activated.value,
    AnalyticsEventName.subscription_renewed.value,
}
_USAGE_EVENT_NAMES = {
    AnalyticsEventName.scenario_run.value,
    AnalyticsEventName.scenario_resumed.value,
    AnalyticsEventName.scenario_completed.value,
    AnalyticsEventName.onboarding_first_action.value,
}
_UPGRADE_EVENT_NAMES = {
    AnalyticsEventName.upgrade_clicked.value,
    AnalyticsEventName.scenario_upgrade_clicked.value,
    AnalyticsEventName.checkout_started.value,
}
_FUNNEL_STEPS: tuple[tuple[str, str, set[str]], ...] = (
    ("acquired", "Acquired", {AnalyticsEventName.user_acquired.value}),
    ("signed_up", "Signed up", {AnalyticsEventName.signup_completed.value}),
    ("activated", "Activated", {AnalyticsEventName.scenario_run.value, AnalyticsEventName.onboarding_first_action.value}),
    ("used", "Used", {AnalyticsEventName.scenario_saved.value, AnalyticsEventName.scenario_completed.value, AnalyticsEventName.scenario_resumed.value}),
    ("upgraded", "Upgraded", set(_UPGRADE_EVENT_NAMES)),
    ("paid", "Paid", set(_PAID_EVENT_NAMES)),
    ("retained", "Retained", {AnalyticsEventName.scenario_resumed.value, AnalyticsEventName.scenario_completed.value}),
)
_PAYWALL_EXPERIMENTS = ("paywall_variant_v1", "pricing_variant_v1")


@dataclass(slots=True)
class _CohortAccumulator:
    users: int = 0
    paid_users: int = 0
    revenue_usd: float = 0.0
    retention_hits: int = 0
    retention_denominator: int = 0
    conversion_lag_sum: float = 0.0
    conversion_lag_count: int = 0


class RevenueOpsService:
    def __init__(
        self,
        *,
        analytics_repo: AnalyticsRepository,
        billing_repo: BillingRepository,
        analytics: AnalyticsService,
        settings: Settings,
    ) -> None:
        self._analytics_repo = analytics_repo
        self._billing_repo = billing_repo
        self._analytics = analytics
        self._settings = settings

    def _percent(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)

    def _safe_source(self, value: str | None) -> str:
        if value is None:
            return "direct"
        normalized = value.strip().lower()
        return normalized or "direct"

    def _week_start(self, day: date) -> date:
        return day - timedelta(days=day.weekday())

    async def dashboard(
        self,
        *,
        user: User | None,
        window_days: int,
    ) -> RevenueDashboardRead:
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

        event_names = {
            *{step_event for _key, _label, events in _FUNNEL_STEPS for step_event in events},
            AnalyticsEventName.paywall_viewed.value,
            AnalyticsEventName.paywall_interaction.value,
            AnalyticsEventName.pricing_plan_selected.value,
            AnalyticsEventName.subscription_canceled.value,
            AnalyticsEventName.churn_risk_detected.value,
            AnalyticsEventName.reactivation_trigger.value,
        }
        rows = await self._analytics_repo.list_event_rows(
            from_ts=from_ts,
            to_ts=now,
            event_names=sorted(event_names),
            user_only=True,
        )
        subscriptions = await self._billing_repo.list_subscriptions()

        all_user_ids = {
            str(user_id) for user_id, _session_id, _event_name, _occurred_at, _metadata in rows if user_id is not None
        }
        all_user_ids.update(str(sub.user_id) for sub in subscriptions)
        attributions = await self._analytics_repo.list_user_attributions(
            user_ids=[uuid.UUID(user_id) for user_id in all_user_ids] if all_user_ids else []
        )
        source_by_user = {
            str(row.user_id): self._safe_source(row.first_utm_source or row.last_utm_source)
            for row in attributions
        }

        first_event_at_by_user: dict[str, dict[str, datetime]] = defaultdict(dict)
        event_times_by_user: dict[str, list[tuple[str, datetime, dict]]] = defaultdict(list)
        for user_id, _session_id, event_name, occurred_at, metadata in rows:
            if user_id is None:
                continue
            key = str(user_id)
            event_times_by_user[key].append((event_name, occurred_at, metadata))
            first = first_event_at_by_user[key].get(event_name)
            if first is None or occurred_at < first:
                first_event_at_by_user[key][event_name] = occurred_at

        paying_subscriptions = [sub for sub in subscriptions if sub.status in _ACTIVE_SUB_STATUSES and sub.plan is not None]
        paying_users = {str(sub.user_id) for sub in paying_subscriptions}
        mrr_usd = round(sum(float(sub.plan.price_usd_month) for sub in paying_subscriptions), 2)
        arr_usd = round(mrr_usd * 12, 2)
        arpu_usd = round(mrr_usd / max(1, len(paying_users)), 2)

        activated_users = {
            user_id
            for user_id, events in first_event_at_by_user.items()
            if any(event_name in _USAGE_EVENT_NAMES for event_name in events.keys())
        }
        paid_users_window = {
            user_id
            for user_id, events in first_event_at_by_user.items()
            if any(event_name in _PAID_EVENT_NAMES for event_name in events.keys())
        }
        canceled_users_window = {
            user_id
            for user_id, events in first_event_at_by_user.items()
            if AnalyticsEventName.subscription_canceled.value in events
        }

        signup_users = {
            user_id
            for user_id, events in first_event_at_by_user.items()
            if AnalyticsEventName.signup_completed.value in events
        }
        revenue_per_user_usd = round(mrr_usd / max(1, len(activated_users)), 2)
        churn_rate = self._percent(len(canceled_users_window), max(1, len(paying_users) + len(canceled_users_window)))
        ltv_proxy_usd = round(arpu_usd * (100.0 / max(churn_rate, 1.0)), 2)

        paid_start_by_user: dict[str, datetime] = {}
        retention_hits = 0
        retention_denominator = 0
        for user_id, timeline in event_times_by_user.items():
            paid_start = min((occurred for name, occurred, _meta in timeline if name in _PAID_EVENT_NAMES), default=None)
            if paid_start is None:
                continue
            paid_start_by_user[user_id] = paid_start
            d30_marker = paid_start + timedelta(days=30)
            if now < d30_marker:
                continue
            retention_denominator += 1
            has_retained_activity = any(name in _USAGE_EVENT_NAMES and occurred >= d30_marker for name, occurred, _meta in timeline)
            if has_retained_activity:
                retention_hits += 1
        paying_retention_d30 = self._percent(retention_hits, retention_denominator)

        headline = RevenueHeadlineRead(
            window_days=window_days,
            computed_at=now,
            mrr_usd=mrr_usd,
            arr_usd=arr_usd,
            arpu_usd=arpu_usd,
            free_to_paid_conversion=self._percent(len(paid_users_window), max(1, len(activated_users))),
            revenue_per_user_usd=revenue_per_user_usd,
            ltv_proxy_usd=ltv_proxy_usd,
            churn_rate=churn_rate,
            paying_user_retention_d30=paying_retention_d30,
        )

        funnel = self._build_funnel(first_event_at_by_user=first_event_at_by_user)
        source_metrics = self._source_metrics(
            source_by_user=source_by_user,
            signup_users=signup_users,
            paid_users=paid_users_window,
            subscriptions=paying_subscriptions,
        )
        cohorts = self._cohorts(
            now=now,
            source_by_user=source_by_user,
            first_event_at_by_user=first_event_at_by_user,
            event_times_by_user=event_times_by_user,
            subscriptions=paying_subscriptions,
            paid_start_by_user=paid_start_by_user,
        )
        paywall_performance = self._paywall_performance(
            event_times_by_user=event_times_by_user,
            paid_users=paid_users_window,
            subscriptions=paying_subscriptions,
        )
        churn = await self._churn_signals(
            now=now,
            event_times_by_user=event_times_by_user,
            paying_users=paying_users,
            canceled_users=canceled_users_window,
        )

        return RevenueDashboardRead(
            headline=headline,
            funnel=funnel,
            funnel_by_source=source_metrics,
            revenue_by_source=source_metrics,
            paywall_performance=paywall_performance,
            cohorts=cohorts,
            churn_signals=churn,
        )

    def _build_funnel(self, *, first_event_at_by_user: dict[str, dict[str, datetime]]) -> RevenueFunnelRead:
        user_state: dict[str, datetime | None] = {user_id: None for user_id in first_event_at_by_user}
        steps: list[RevenueFunnelStepRead] = []
        previous_count = 0
        for index, (step_key, label, event_names) in enumerate(_FUNNEL_STEPS):
            reached: set[str] = set()
            for user_id, events in first_event_at_by_user.items():
                candidate_times = [events[event_name] for event_name in event_names if event_name in events]
                if not candidate_times:
                    continue
                candidate_time = min(candidate_times)
                if index == 0:
                    reached.add(user_id)
                    user_state[user_id] = candidate_time
                    continue
                prev_time = user_state.get(user_id)
                if prev_time is None or candidate_time < prev_time:
                    continue
                reached.add(user_id)
                user_state[user_id] = candidate_time

            count = len(reached)
            conversion = 100.0 if index == 0 else self._percent(count, max(1, previous_count))
            dropoff = 0.0 if index == 0 else round(max(0.0, 100.0 - conversion), 2)
            steps.append(
                RevenueFunnelStepRead(
                    key=step_key,
                    label=label,
                    users=count,
                    conversion_from_prev=conversion,
                    dropoff_from_prev=dropoff,
                )
            )
            previous_count = count
        return RevenueFunnelRead(steps=steps)

    def _source_metrics(
        self,
        *,
        source_by_user: dict[str, str],
        signup_users: set[str],
        paid_users: set[str],
        subscriptions: list,
    ) -> list[RevenueSourceRead]:
        signup_by_source: dict[str, set[str]] = defaultdict(set)
        paid_by_source: dict[str, set[str]] = defaultdict(set)
        mrr_by_source: dict[str, float] = defaultdict(float)

        for user_id in signup_users:
            source = source_by_user.get(user_id, "direct")
            signup_by_source[source].add(user_id)
        for user_id in paid_users:
            source = source_by_user.get(user_id, "direct")
            paid_by_source[source].add(user_id)
        for sub in subscriptions:
            source = source_by_user.get(str(sub.user_id), "direct")
            mrr_by_source[source] += float(sub.plan.price_usd_month)

        sources = sorted(set(signup_by_source) | set(paid_by_source) | set(mrr_by_source))
        rows: list[RevenueSourceRead] = []
        for source in sources:
            acquired = len(signup_by_source.get(source, set()))
            paid = len(paid_by_source.get(source, set()))
            mrr = round(mrr_by_source.get(source, 0.0), 2)
            rows.append(
                RevenueSourceRead(
                    source=source,
                    acquired_users=acquired,
                    paid_users=paid,
                    conversion_rate=self._percent(paid, max(1, acquired)),
                    mrr_usd=mrr,
                    arr_usd=round(mrr * 12, 2),
                )
            )
        rows.sort(key=lambda item: item.mrr_usd, reverse=True)
        return rows[:12]

    def _cohorts(
        self,
        *,
        now: datetime,
        source_by_user: dict[str, str],
        first_event_at_by_user: dict[str, dict[str, datetime]],
        event_times_by_user: dict[str, list[tuple[str, datetime, dict]]],
        subscriptions: list,
        paid_start_by_user: dict[str, datetime],
    ) -> list[RevenueCohortRead]:
        plan_by_user: dict[str, str] = {}
        price_by_user: dict[str, float] = {}
        for sub in subscriptions:
            key = str(sub.user_id)
            plan_by_user[key] = sub.plan.tier.value if sub.plan else PlanTier.free.value
            price_by_user[key] = float(sub.plan.price_usd_month if sub.plan else 0)

        cohorts: dict[tuple[date, str, str], _CohortAccumulator] = defaultdict(_CohortAccumulator)
        for user_id, events in first_event_at_by_user.items():
            acquired_at = events.get(AnalyticsEventName.user_acquired.value) or events.get(AnalyticsEventName.signup_completed.value)
            if acquired_at is None:
                continue
            source = source_by_user.get(user_id, "direct")
            plan_tier = plan_by_user.get(user_id, PlanTier.free.value)
            key = (self._week_start(acquired_at.date()), source, plan_tier)
            item = cohorts[key]
            item.users += 1

            paid_at = paid_start_by_user.get(user_id)
            if paid_at is not None:
                item.paid_users += 1
                item.conversion_lag_sum += max((paid_at - acquired_at).total_seconds() / 86400.0, 0.0)
                item.conversion_lag_count += 1
            item.revenue_usd += price_by_user.get(user_id, 0.0)

            d30_marker = acquired_at + timedelta(days=30)
            if now >= d30_marker:
                item.retention_denominator += 1
                has_d30_usage = any(
                    name in _USAGE_EVENT_NAMES and occurred >= d30_marker
                    for name, occurred, _meta in event_times_by_user.get(user_id, [])
                )
                if has_d30_usage:
                    item.retention_hits += 1

        rows: list[RevenueCohortRead] = []
        for (week_start, source, plan_tier), item in sorted(cohorts.items(), key=lambda pair: pair[0][0], reverse=True):
            rows.append(
                RevenueCohortRead(
                    cohort_week_start=week_start,
                    source=source,
                    plan_tier=plan_tier,
                    users=item.users,
                    paid_users=item.paid_users,
                    revenue_usd=round(item.revenue_usd, 2),
                    retention_d30=(
                        self._percent(item.retention_hits, item.retention_denominator)
                        if item.retention_denominator > 0
                        else None
                    ),
                    conversion_lag_days=(
                        round(item.conversion_lag_sum / item.conversion_lag_count, 2)
                        if item.conversion_lag_count > 0
                        else None
                    ),
                )
            )
        return rows[:20]

    def _paywall_performance(
        self,
        *,
        event_times_by_user: dict[str, list[tuple[str, datetime, dict]]],
        paid_users: set[str],
        subscriptions: list,
    ) -> list[RevenueExperimentVariantRead]:
        mrr_by_user = {str(sub.user_id): float(sub.plan.price_usd_month if sub.plan else 0) for sub in subscriptions}
        assignments: dict[tuple[str, str], set[str]] = defaultdict(set)
        views: dict[tuple[str, str], set[str]] = defaultdict(set)
        interactions: dict[tuple[str, str], set[str]] = defaultdict(set)
        upgrades: dict[tuple[str, str], set[str]] = defaultdict(set)
        retention: dict[tuple[str, str], set[str]] = defaultdict(set)

        for user_id, timeline in event_times_by_user.items():
            latest_variant_by_exp: dict[str, str] = {}
            for event_name, _occurred_at, metadata in timeline:
                paywall_variant = str(metadata.get("paywall_variant") or "").strip()
                pricing_variant = str(metadata.get("pricing_variant") or "").strip()
                if paywall_variant:
                    latest_variant_by_exp["paywall_variant_v1"] = paywall_variant
                if pricing_variant:
                    latest_variant_by_exp["pricing_variant_v1"] = pricing_variant

                for experiment_key in _PAYWALL_EXPERIMENTS:
                    variant = latest_variant_by_exp.get(experiment_key)
                    if not variant:
                        continue
                    key = (experiment_key, variant)
                    assignments[key].add(user_id)
                    if event_name == AnalyticsEventName.paywall_viewed.value:
                        views[key].add(user_id)
                    if event_name in {
                        AnalyticsEventName.paywall_interaction.value,
                        AnalyticsEventName.pricing_plan_selected.value,
                    }:
                        interactions[key].add(user_id)
                    if event_name in _UPGRADE_EVENT_NAMES:
                        upgrades[key].add(user_id)
                    if event_name in _USAGE_EVENT_NAMES:
                        retention[key].add(user_id)

        rows: list[RevenueExperimentVariantRead] = []
        keys = sorted(assignments.keys())
        for experiment_key, variant in keys:
            assigned_users = assignments[(experiment_key, variant)]
            paid_variant_users = assigned_users & paid_users
            revenue_sum = sum(mrr_by_user.get(user_id, 0.0) for user_id in paid_variant_users)
            rows.append(
                RevenueExperimentVariantRead(
                    experiment_key=experiment_key,
                    variant=variant,
                    views=len(views[(experiment_key, variant)]),
                    interactions=len(interactions[(experiment_key, variant)]),
                    upgrades=len(upgrades[(experiment_key, variant)]),
                    paid_users=len(paid_variant_users),
                    conversion_rate=self._percent(len(paid_variant_users), max(1, len(assigned_users))),
                    revenue_per_user_usd=round(revenue_sum / max(1, len(assigned_users)), 2),
                    retention_d30=self._percent(len(retention[(experiment_key, variant)]), max(1, len(assigned_users))),
                )
            )
        rows.sort(key=lambda item: (item.experiment_key, -item.revenue_per_user_usd, -item.conversion_rate))
        return rows

    async def _churn_signals(
        self,
        *,
        now: datetime,
        event_times_by_user: dict[str, list[tuple[str, datetime, dict]]],
        paying_users: set[str],
        canceled_users: set[str],
    ) -> RevenueChurnSignalRead:
        inactivity_cutoff = now - timedelta(days=7)
        inactive_paying_users: set[str] = set()
        for user_id in paying_users:
            timeline = event_times_by_user.get(user_id, [])
            last_usage = max((occurred for name, occurred, _meta in timeline if name in _USAGE_EVENT_NAMES), default=None)
            if last_usage is None or last_usage < inactivity_cutoff:
                inactive_paying_users.add(user_id)

        risk_users = inactive_paying_users | canceled_users
        for user_id in risk_users:
            reason = "canceled_subscription" if user_id in canceled_users else "inactive_paying_user"
            attribution = await self._analytics.get_user_last_touch_attribution(user_id=uuid.UUID(user_id))
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.churn_risk_detected,
                user_id=uuid.UUID(user_id),
                event_id=f"churn_risk:{user_id}:{reason}:{now.date().isoformat()}",
                metadata={
                    "reason": reason,
                    "window_days": 7,
                },
                attribution=attribution,
                context_page="/api/v1/analytics/revenue/dashboard",
                context_feature="churn_detection",
            )
            if reason == "canceled_subscription":
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.reactivation_trigger,
                    user_id=uuid.UUID(user_id),
                    event_id=f"reactivation_trigger:{user_id}:{now.date().isoformat()}",
                    metadata={"reason": "subscription_canceled"},
                    attribution=attribution,
                    context_page="/api/v1/analytics/revenue/dashboard",
                    context_feature="reactivation",
                )

        return RevenueChurnSignalRead(
            churn_risk_users=len(risk_users),
            canceled_users=len(canceled_users),
            inactive_paying_users=len(inactive_paying_users),
            generated_at=now,
        )
