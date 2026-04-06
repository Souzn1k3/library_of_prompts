from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.config import Settings
from app.core.errors import AppError
from app.infrastructure.db.models import PlanTier, User, UserRole
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.model.growth import (
    GrowthCohortRead,
    GrowthDashboardRead,
    GrowthExperimentAssignmentRead,
    GrowthExperimentRead,
    GrowthExperimentVariantRead,
    GrowthFlagRead,
    GrowthFunnelRead,
    GrowthFunnelStepRead,
    GrowthMetricSnapshotRead,
    GrowthRuntimeRead,
)
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService

_ACTIVATION_EVENTS = {"scenario_run", "onboarding_first_action"}
_RETENTION_EVENTS = {"scenario_run", "scenario_resumed", "scenario_completed"}
_UPGRADE_INTENT_EVENTS = {"upgrade_clicked", "scenario_upgrade_clicked", "checkout_started"}
_PAID_EVENTS = {"subscription_activated"}
_STORE_PURCHASE_EVENTS = {"store_purchase_completed"}

_FUNNEL_STEPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("signup", "Sign up", ("signup_completed",)),
    ("activated", "First value", ("scenario_run", "onboarding_first_action")),
    ("saved", "Saved scenario", ("scenario_saved",)),
    ("resumed", "Returned to scenario", ("scenario_resumed", "scenario_completed")),
    ("paid", "Paid conversion", ("subscription_activated",)),
)


@dataclass(frozen=True, slots=True)
class _FlagDefinition:
    key: str
    target: str
    rollout_percent: int


@dataclass(frozen=True, slots=True)
class _ExperimentDefinition:
    key: str
    target: str
    rollout_percent: int
    variants: tuple[tuple[str, int], ...]


class GrowthOpsService:
    def __init__(
        self,
        *,
        repo: AnalyticsRepository,
        analytics: AnalyticsService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._analytics = analytics
        self._settings = settings

    def _flag_definitions(self) -> tuple[_FlagDefinition, ...]:
        return (
            _FlagDefinition(
                key="growth_dashboard",
                target="authenticated",
                rollout_percent=int(self._settings.growth_flag_dashboard_rollout_percent),
            ),
            _FlagDefinition(
                key="scenario_chain_recommendations",
                target="all",
                rollout_percent=int(self._settings.growth_flag_chain_recommendations_rollout_percent),
            ),
            _FlagDefinition(
                key="showcase_share_prompts",
                target="all",
                rollout_percent=int(self._settings.growth_flag_showcase_share_rollout_percent),
            ),
        )

    def _experiment_definitions(self) -> tuple[_ExperimentDefinition, ...]:
        return (
            _ExperimentDefinition(
                key="homepage_entry_v2",
                target="all",
                rollout_percent=int(self._settings.growth_experiment_homepage_rollout_percent),
                variants=(
                    ("control", 50),
                    ("treatment", 50),
                ),
            ),
            _ExperimentDefinition(
                key="scenario_upgrade_moment_v1",
                target="authenticated",
                rollout_percent=int(self._settings.growth_experiment_upgrade_rollout_percent),
                variants=(
                    ("control", 50),
                    ("treatment", 50),
                ),
            ),
            _ExperimentDefinition(
                key="paywall_variant_v1",
                target="all",
                rollout_percent=int(self._settings.growth_experiment_paywall_rollout_percent),
                variants=(
                    ("soft", 50),
                    ("value_focused", 50),
                ),
            ),
            _ExperimentDefinition(
                key="pricing_variant_v1",
                target="all",
                rollout_percent=int(self._settings.growth_experiment_pricing_rollout_percent),
                variants=(
                    ("standard", 50),
                    ("operator_pack", 50),
                ),
            ),
        )

    def _subject_key(self, *, user: User | None, session_id: str) -> str:
        normalized_session = session_id.strip() or "guest"
        return str(user.id) if user is not None else normalized_session

    def _bucket(self, *, seed: str, modulo: int) -> int:
        if modulo <= 0:
            return 0
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return int(digest[:12], 16) % modulo

    def _is_eligible(self, *, target: str, user: User | None) -> bool:
        if target == "all":
            return True
        if target == "guest":
            return user is None
        if target == "authenticated":
            return user is not None
        if user is None:
            return False
        if target == "free":
            return user.plan_tier == PlanTier.free
        if target == "pro":
            return user.plan_tier != PlanTier.free
        return False

    def _safe_rollout_percent(self, value: int) -> int:
        return max(0, min(100, int(value)))

    def _percent(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)

    async def runtime_decisions(
        self,
        *,
        user: User | None,
        session_id: str,
        page: str,
        feature: str,
    ) -> GrowthRuntimeRead:
        now = datetime.now(timezone.utc)
        subject = self._subject_key(user=user, session_id=session_id)
        subject_hash = hashlib.sha1(subject.encode("utf-8")).hexdigest()[:12]

        flags: list[GrowthFlagRead] = []
        for definition in self._flag_definitions():
            eligible = self._is_eligible(target=definition.target, user=user)
            rollout_percent = self._safe_rollout_percent(definition.rollout_percent)
            seed = f"flag:{definition.key}:{subject}"
            enabled = eligible and self._bucket(seed=seed, modulo=100) < rollout_percent
            reason = (
                "not_eligible"
                if not eligible
                else ("enabled_by_rollout" if enabled else "outside_rollout")
            )
            flags.append(
                GrowthFlagRead(
                    key=definition.key,
                    enabled=enabled,
                    rollout_percent=rollout_percent,
                    target=definition.target,
                    reason=reason,
                )
            )
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.feature_flag_exposed,
                user_id=user.id if user else None,
                event_id=f"flag_exposed:{definition.key}:{subject_hash}:{now.date().isoformat()}",
                metadata={
                    "flag_key": definition.key,
                    "enabled": enabled,
                    "rollout_percent": rollout_percent,
                    "target": definition.target,
                    "reason": reason,
                    "session_id": session_id,
                },
                context_page=page,
                context_feature=feature,
            )

        experiments: list[GrowthExperimentAssignmentRead] = []
        for definition in self._experiment_definitions():
            eligible = self._is_eligible(target=definition.target, user=user)
            rollout_percent = self._safe_rollout_percent(definition.rollout_percent)
            in_rollout = eligible and self._bucket(seed=f"exp:{definition.key}:{subject}", modulo=100) < rollout_percent
            variant = "control"
            if in_rollout:
                weights = [(name, max(weight, 0)) for name, weight in definition.variants]
                total_weight = sum(weight for _name, weight in weights)
                if total_weight > 0:
                    roll = self._bucket(seed=f"exp_variant:{definition.key}:{subject}", modulo=total_weight)
                    cursor = 0
                    for name, weight in weights:
                        cursor += weight
                        if roll < cursor:
                            variant = name
                            break
            reason = (
                "not_eligible"
                if not eligible
                else ("in_rollout" if in_rollout else "outside_rollout")
            )
            experiments.append(
                GrowthExperimentAssignmentRead(
                    key=definition.key,
                    variant=variant,
                    rollout_percent=rollout_percent,
                    eligible=eligible,
                    reason=reason,
                )
            )
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.growth_experiment_assigned,
                user_id=user.id if user else None,
                event_id=f"growth_exp_assigned:{definition.key}:{subject_hash}:{now.date().isoformat()}",
                metadata={
                    "experiment_name": definition.key,
                    "experiment_variant": variant,
                    "eligible": eligible,
                    "rollout_percent": rollout_percent,
                    "target": definition.target,
                    "reason": reason,
                    "session_id": session_id,
                },
                context_page=page,
                context_feature=feature,
            )

        return GrowthRuntimeRead(
            computed_at=now,
            session_id=session_id,
            flags=flags,
            experiments=experiments,
        )

    async def dashboard(
        self,
        *,
        user: User | None,
        window_days: int,
    ) -> GrowthDashboardRead:
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

        relevant_events = {
            "signup_completed",
            *_ACTIVATION_EVENTS,
            *_RETENTION_EVENTS,
            *_UPGRADE_INTENT_EVENTS,
            *_PAID_EVENTS,
            *_STORE_PURCHASE_EVENTS,
            "scenario_saved",
            AnalyticsEventName.growth_experiment_assigned.value,
            AnalyticsEventName.feature_flag_exposed.value,
        }
        rows = await self._repo.list_event_rows(
            from_ts=from_ts,
            to_ts=now,
            event_names=sorted(relevant_events),
            user_only=True,
        )
        metrics = self._build_metrics(rows=rows, now=now, window_days=window_days)
        funnel = self._build_funnel(rows=rows, window_days=window_days)
        cohorts = self._build_cohorts(rows=rows, now=now, window_days=window_days)
        experiments = self._build_experiment_summary(rows=rows, now=now)

        rollout_flags = [
            GrowthFlagRead(
                key=definition.key,
                enabled=definition.rollout_percent > 0,
                rollout_percent=self._safe_rollout_percent(definition.rollout_percent),
                target=definition.target,
                reason="configured_rollout",
            )
            for definition in self._flag_definitions()
        ]
        return GrowthDashboardRead(
            metrics=metrics,
            funnel=funnel,
            cohorts=cohorts,
            experiments=experiments,
            rollout_flags=rollout_flags,
        )

    def _build_metrics(
        self,
        *,
        rows: Iterable[tuple[object, str, str, datetime, dict[str, object]]],
        now: datetime,
        window_days: int,
    ) -> GrowthMetricSnapshotRead:
        signup_at: dict[str, datetime] = {}
        activation_at: dict[str, datetime] = {}
        retention_dates: dict[str, set[datetime.date]] = {}
        active_users: set[str] = set()
        intent_users: set[str] = set()
        paid_users: set[str] = set()
        store_users: set[str] = set()

        for user_id, _session_id, event_name, occurred_at, _metadata in rows:
            if user_id is None:
                continue
            key = str(user_id)
            if event_name == "signup_completed":
                signup_at[key] = min(signup_at.get(key, occurred_at), occurred_at)
            if event_name in _ACTIVATION_EVENTS:
                activation_at[key] = min(activation_at.get(key, occurred_at), occurred_at)
                active_users.add(key)
            if event_name in _RETENTION_EVENTS:
                retention_dates.setdefault(key, set()).add(occurred_at.date())
                active_users.add(key)
            if event_name in _UPGRADE_INTENT_EVENTS:
                intent_users.add(key)
            if event_name in _PAID_EVENTS:
                paid_users.add(key)
            if event_name in _STORE_PURCHASE_EVENTS:
                store_users.add(key)

        activated_from_signup = 0
        d1_retained = 0
        d7_retained = 0
        for user_key, signup_time in signup_at.items():
            activation_time = activation_at.get(user_key)
            if activation_time and activation_time <= signup_time + timedelta(hours=24):
                activated_from_signup += 1
            events_by_date = retention_dates.get(user_key, set())
            if signup_time.date() + timedelta(days=1) in events_by_date:
                d1_retained += 1
            if signup_time.date() + timedelta(days=7) in events_by_date:
                d7_retained += 1

        signup_count = len(signup_at)
        paid_count = len(paid_users)
        paid_and_store_value = (paid_count * 29) + (len(store_users) * 4)

        return GrowthMetricSnapshotRead(
            window_days=window_days,
            computed_at=now,
            activation_rate=self._percent(activated_from_signup, signup_count),
            d1_retention=self._percent(d1_retained, signup_count),
            d7_retention=self._percent(d7_retained, signup_count),
            free_to_paid_conversion=self._percent(paid_count, max(1, len(active_users))),
            upgrade_intent_rate=self._percent(len(intent_users), max(1, len(active_users))),
            ltv_proxy_usd=round(paid_and_store_value / max(signup_count, 1), 2),
        )

    def _build_funnel(
        self,
        *,
        rows: Iterable[tuple[object, str, str, datetime, dict[str, object]]],
        window_days: int,
    ) -> GrowthFunnelRead:
        step_event_sets = [set(definition[2]) for definition in _FUNNEL_STEPS]
        step_times: dict[str, list[datetime | None]] = {}

        for user_id, _session_id, event_name, occurred_at, _metadata in rows:
            if user_id is None:
                continue
            key = str(user_id)
            if key not in step_times:
                step_times[key] = [None for _ in _FUNNEL_STEPS]
            for index, event_set in enumerate(step_event_sets):
                if event_name not in event_set:
                    continue
                current = step_times[key][index]
                if current is None or occurred_at < current:
                    step_times[key][index] = occurred_at

        reached_prev: dict[str, datetime] = {}
        steps: list[GrowthFunnelStepRead] = []
        for index, (step_key, label, _events) in enumerate(_FUNNEL_STEPS):
            reached_curr: dict[str, datetime] = {}
            if index == 0:
                for user_key, timeline in step_times.items():
                    when = timeline[index]
                    if when is not None:
                        reached_curr[user_key] = when
                conversion_from_prev = 100.0 if reached_curr else 0.0
            else:
                for user_key, prev_time in reached_prev.items():
                    when = step_times[user_key][index]
                    if when is None or when < prev_time:
                        continue
                    reached_curr[user_key] = when
                conversion_from_prev = self._percent(len(reached_curr), max(1, len(reached_prev)))

            steps.append(
                GrowthFunnelStepRead(
                    key=step_key,
                    label=label,
                    users=len(reached_curr),
                    conversion_from_prev=conversion_from_prev,
                )
            )
            reached_prev = reached_curr

        return GrowthFunnelRead(window_days=window_days, steps=steps)

    def _build_cohorts(
        self,
        *,
        rows: Iterable[tuple[object, str, str, datetime, dict[str, object]]],
        now: datetime,
        window_days: int,
    ) -> list[GrowthCohortRead]:
        signup_dates: dict[str, datetime.date] = {}
        active_dates: dict[str, set[datetime.date]] = {}
        paid_dates: dict[str, list[datetime.date]] = {}

        for user_id, _session_id, event_name, occurred_at, _metadata in rows:
            if user_id is None:
                continue
            key = str(user_id)
            if event_name == "signup_completed":
                current = signup_dates.get(key)
                if current is None or occurred_at.date() < current:
                    signup_dates[key] = occurred_at.date()
            if event_name in _RETENTION_EVENTS:
                active_dates.setdefault(key, set()).add(occurred_at.date())
            if event_name in _PAID_EVENTS:
                paid_dates.setdefault(key, []).append(occurred_at.date())

        cohorts: dict[datetime.date, dict[str, int]] = {}
        for user_key, signup_day in signup_dates.items():
            week_start = signup_day - timedelta(days=signup_day.weekday())
            bucket = cohorts.setdefault(
                week_start,
                {
                    "users": 0,
                    "d1_hits": 0,
                    "d7_hits": 0,
                    "d7_denominator": 0,
                    "paid_30d_hits": 0,
                    "paid_30d_denominator": 0,
                },
            )
            bucket["users"] += 1
            user_active_dates = active_dates.get(user_key, set())
            if signup_day + timedelta(days=1) in user_active_dates:
                bucket["d1_hits"] += 1

            d7_day = signup_day + timedelta(days=7)
            if now.date() >= d7_day:
                bucket["d7_denominator"] += 1
                if d7_day in user_active_dates:
                    bucket["d7_hits"] += 1

            paid_days = paid_dates.get(user_key, [])
            paid_limit = signup_day + timedelta(days=30)
            if now.date() >= paid_limit:
                bucket["paid_30d_denominator"] += 1
                if any(signup_day <= paid_day <= paid_limit for paid_day in paid_days):
                    bucket["paid_30d_hits"] += 1

        min_week_start = (now - timedelta(days=window_days)).date() - timedelta(days=6)
        items: list[GrowthCohortRead] = []
        for week_start, stats in sorted(cohorts.items(), key=lambda item: item[0], reverse=True):
            if week_start < min_week_start:
                continue
            d7_retention = (
                self._percent(stats["d7_hits"], stats["d7_denominator"])
                if stats["d7_denominator"] > 0
                else None
            )
            paid_30d_conversion = (
                self._percent(stats["paid_30d_hits"], stats["paid_30d_denominator"])
                if stats["paid_30d_denominator"] > 0
                else None
            )
            items.append(
                GrowthCohortRead(
                    cohort_week_start=week_start,
                    users=stats["users"],
                    d1_retention=self._percent(stats["d1_hits"], stats["users"]),
                    d7_retention=d7_retention,
                    paid_30d_conversion=paid_30d_conversion,
                )
            )
        return items

    def _build_experiment_summary(
        self,
        *,
        rows: Iterable[tuple[object, str, str, datetime, dict[str, object]]],
        now: datetime,
    ) -> list[GrowthExperimentRead]:
        assignments: dict[str, dict[str, set[str]]] = {}
        paid_users: set[str] = set()
        retained_users: set[str] = set()

        for user_id, _session_id, event_name, occurred_at, metadata in rows:
            if user_id is None:
                continue
            user_key = str(user_id)
            if event_name in _PAID_EVENTS:
                paid_users.add(user_key)
            if event_name in _RETENTION_EVENTS and occurred_at.date() >= (now.date() - timedelta(days=7)):
                retained_users.add(user_key)
            if event_name != AnalyticsEventName.growth_experiment_assigned.value:
                continue
            experiment_name = str(metadata.get("experiment_name") or "").strip()
            variant = str(metadata.get("experiment_variant") or "control").strip() or "control"
            if not experiment_name:
                continue
            assignments.setdefault(experiment_name, {}).setdefault(variant, set()).add(user_key)

        reads: list[GrowthExperimentRead] = []
        for definition in self._experiment_definitions():
            by_variant = assignments.get(definition.key, {})
            variants: list[GrowthExperimentVariantRead] = []
            for variant_name, _weight in definition.variants:
                users = by_variant.get(variant_name, set())
                variants.append(
                    GrowthExperimentVariantRead(
                        variant=variant_name,
                        users=len(users),
                        conversion=self._percent(len(users & paid_users), max(1, len(users))),
                        retention_d7=self._percent(len(users & retained_users), max(1, len(users))),
                    )
                )
            reads.append(
                GrowthExperimentRead(
                    key=definition.key,
                    rollout_percent=self._safe_rollout_percent(definition.rollout_percent),
                    variants=variants,
                )
            )
        return reads
