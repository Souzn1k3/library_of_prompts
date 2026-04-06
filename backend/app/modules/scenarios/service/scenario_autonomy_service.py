from __future__ import annotations

import hashlib
import re
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import Settings
from app.core.errors import AppError
from app.infrastructure.db.models import (
    ScenarioAutonomyCycle,
    ScenarioAutonomyExperiment,
    ScenarioAutonomyGrowthDecision,
    ScenarioAutonomyGuardrailEvent,
    ScenarioAutonomyPersonalizationProfile,
    SubscriptionStatus,
    User,
    UserScenarioBlueprint,
)
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.scenarios.model.scenario import (
    ScenarioAutonomyCycleRead,
    ScenarioAutonomyExperimentRead,
    ScenarioAutonomyGrowthDecisionRead,
    ScenarioAutonomyGuardrailRead,
    ScenarioAutonomyNeedSignalRead,
    ScenarioAutonomyPersonalizationRead,
    ScenarioAutonomySelfCheckRead,
    ScenarioAutonomyStatusRead,
    ScenarioBlueprintPatchWrite,
    ScenarioBlueprintRead,
    ScenarioBlueprintWrite,
)
from app.modules.scenarios.repository.scenario_platform_repository import ScenarioPlatformRepository
from app.modules.scenarios.service.scenario_platform_service import ScenarioPlatformService

_ACTIVE_SUB_STATUSES = (
    SubscriptionStatus.active,
    SubscriptionStatus.trialing,
    SubscriptionStatus.past_due,
)
_RETENTION_EVENTS = {
    AnalyticsEventName.scenario_resumed.value,
    AnalyticsEventName.scenario_completed.value,
    AnalyticsEventName.subscription_activated.value,
}


@dataclass(frozen=True, slots=True)
class _NeedSignal:
    source: str
    key: str
    strength: float
    evidence_count: int


def _clean_phrase(value: str, *, fallback: str = "autonomous") -> str:
    normalized = re.sub(r"[^a-z0-9\s-]+", " ", value.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized or fallback


def _slug_fragment(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized[:36] or "autonomous"


def _score_blueprint(row: UserScenarioBlueprint) -> float:
    runs = max(int(row.run_count or 0), 1)
    completion_rate = min(1.0, max(0.0, float(row.completion_count or 0) / float(runs))) * 100.0
    rating_score = min(max(float(row.rating_average or 0.0), 0.0), 5.0) * 20.0
    saves_score = min(float(row.save_count or 0) * 2.5, 30.0)
    run_score = min(float(row.run_count or 0) * 0.6, 20.0)
    blended = completion_rate * 0.45 + rating_score * 0.25 + saves_score * 0.15 + run_score * 0.15
    return round(min(max(blended, 0.0), 100.0), 2)


class ScenarioGenerationEngine:
    def __init__(
        self,
        *,
        repo: ScenarioPlatformRepository,
        analytics_repo: AnalyticsRepository,
        platform: ScenarioPlatformService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._analytics_repo = analytics_repo
        self._platform = platform
        self._settings = settings

    async def _collect_need_signals(self, *, now: datetime) -> list[_NeedSignal]:
        from_ts = now - timedelta(days=max(1, int(self._settings.scenario_autonomy_signal_window_days)))
        rows = await self._analytics_repo.list_event_rows(
            from_ts=from_ts,
            to_ts=now,
            event_names=[
                AnalyticsEventName.catalog_search_used.value,
                AnalyticsEventName.scenario_run.value,
                AnalyticsEventName.scenario_completed.value,
                AnalyticsEventName.scenario_saved.value,
                AnalyticsEventName.scenario_resumed.value,
                AnalyticsEventName.signup_completed.value,
                AnalyticsEventName.subscription_activated.value,
            ],
            user_only=False,
        )

        search_counter: Counter[str] = Counter()
        failed_counter: Counter[str] = Counter()
        popular_counter: Counter[str] = Counter()
        signup_at_by_user: dict[str, datetime] = {}
        retained_users: set[str] = set()

        for user_id, _session_id, event_name, occurred_at, metadata in rows:
            payload = metadata if isinstance(metadata, dict) else {}
            if event_name == AnalyticsEventName.catalog_search_used.value:
                query = str(payload.get("query") or payload.get("search") or payload.get("term") or "").strip()
                if query:
                    search_counter[_clean_phrase(query)[:80]] += 1

            if event_name == AnalyticsEventName.scenario_run.value:
                status = str(payload.get("status") or payload.get("result") or "").strip().lower()
                if status in {"failed", "error", "timeout", "blocked"}:
                    failed_key = str(payload.get("intent") or payload.get("prompt_slug") or "general").strip().lower()
                    failed_counter[_clean_phrase(failed_key, fallback="general")[:80]] += 1

            if event_name in {
                AnalyticsEventName.scenario_run.value,
                AnalyticsEventName.scenario_completed.value,
                AnalyticsEventName.scenario_saved.value,
                AnalyticsEventName.scenario_resumed.value,
            }:
                popular_counter[event_name.replace("scenario_", "")] += 1

            if user_id is None:
                continue
            user_key = str(user_id)
            if event_name == AnalyticsEventName.signup_completed.value:
                existing = signup_at_by_user.get(user_key)
                if existing is None or occurred_at < existing:
                    signup_at_by_user[user_key] = occurred_at
            if event_name in _RETENTION_EVENTS:
                retained_users.add(user_key)

        signals: list[_NeedSignal] = []

        if search_counter:
            max_search = max(search_counter.values())
            for key, count in search_counter.most_common(3):
                signals.append(
                    _NeedSignal(
                        source="search",
                        key=key,
                        strength=min(1.0, max(0.05, count / max(1, max_search))),
                        evidence_count=int(count),
                    )
                )

        if failed_counter:
            max_failed = max(failed_counter.values())
            for key, count in failed_counter.most_common(3):
                signals.append(
                    _NeedSignal(
                        source="failed_runs",
                        key=key,
                        strength=min(1.0, max(0.08, count / max(1, max_failed))),
                        evidence_count=int(count),
                    )
                )

        if popular_counter:
            top_action, count = popular_counter.most_common(1)[0]
            max_popular = max(popular_counter.values())
            signals.append(
                _NeedSignal(
                    source="popular_actions",
                    key=top_action,
                    strength=min(1.0, max(0.05, count / max(1, max_popular))),
                    evidence_count=int(count),
                )
            )

        retention_gap = 0
        retention_cutoff = now - timedelta(days=7)
        for user_key, signed_up_at in signup_at_by_user.items():
            if signed_up_at > retention_cutoff:
                continue
            if user_key not in retained_users:
                retention_gap += 1
        if retention_gap > 0:
            denominator = max(1, len(signup_at_by_user))
            signals.append(
                _NeedSignal(
                    source="retention_gap",
                    key="d7_dropoff_recovery",
                    strength=min(1.0, max(0.1, retention_gap / denominator)),
                    evidence_count=int(retention_gap),
                )
            )

        if not signals:
            signals.append(
                _NeedSignal(
                    source="popular_actions",
                    key="operator-workflow",
                    strength=0.35,
                    evidence_count=1,
                )
            )
        return signals

    def _category_from_signal(self, signal: _NeedSignal) -> str:
        tokens = signal.key.lower()
        if any(token in tokens for token in ("growth", "retention", "conversion", "pricing", "paywall", "revenue")):
            return "growth"
        if any(token in tokens for token in ("learn", "lesson", "study")):
            return "learning"
        if any(token in tokens for token in ("qa", "debug", "workflow", "operator", "analysis")):
            return "productivity"
        return "utility"

    def _dsl_from_signal(self, signal: _NeedSignal, *, cycle_id: uuid.UUID, index: int) -> str:
        intent = _clean_phrase(signal.key)
        return "\n".join(
            [
                "version: v5.autonomous",
                f"cycle_id: {cycle_id}",
                f"signal_source: {signal.source}",
                f"signal_key: {intent}",
                f"variant: draft_{index}",
                "steps:",
                "  - discover_user_intent",
                "  - generate_structured_output",
                "  - run_quality_checks",
                "  - summarize_next_best_action",
                "feedback_loop:",
                "  collect: [conversion, retention, revenue]",
                "  auto_iterate: true",
                "  rollback_on_guardrail: true",
                "personalization:",
                "  adapt_tone_from_user_history: true",
                "  adapt_depth_by_completion_rate: true",
            ]
        )

    def _signal_to_read(self, signal: _NeedSignal) -> ScenarioAutonomyNeedSignalRead:
        return ScenarioAutonomyNeedSignalRead(
            source=signal.source,  # type: ignore[arg-type]
            key=signal.key,
            strength=round(min(max(signal.strength, 0.0), 1.0), 4),
            evidence_count=int(signal.evidence_count),
        )

    async def generate(
        self,
        *,
        owner: User,
        cycle: ScenarioAutonomyCycle,
        max_scenarios: int,
    ) -> tuple[list[ScenarioBlueprintRead], list[ScenarioAutonomyNeedSignalRead]]:
        now = datetime.now(timezone.utc)
        signals = await self._collect_need_signals(now=now)
        selected = signals[: max(1, max_scenarios)]

        generated: list[ScenarioBlueprintRead] = []
        for index, signal in enumerate(selected, start=1):
            signal_key = _slug_fragment(signal.key)
            slug = f"auto-{signal.source}-{signal_key}-{uuid.uuid4().hex[:6]}"
            category = self._category_from_signal(signal)
            metadata: dict[str, Any] = {
                "autonomous": {
                    "enabled": True,
                    "cycle_id": str(cycle.id),
                    "signal_source": signal.source,
                    "signal_key": signal.key,
                    "signal_strength": round(signal.strength, 4),
                    "created_at": now.isoformat(),
                }
            }
            body = ScenarioBlueprintWrite(
                slug=slug,
                title=f"Autonomous {signal.source.replace('_', ' ').title()} - {signal.key[:48]}",
                summary=(
                    "Self-generated scenario from live behavior signals. "
                    "Runs through test -> optimize -> publish automatically."
                ),
                category=category,  # type: ignore[arg-type]
                tags=["autonomous", "v5", signal.source, signal_key],
                metadata=metadata,
                input_schema={
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string"},
                        "context": {"type": "string"},
                    },
                    "required": ["goal"],
                },
                context_text="Auto-generated from demand and retention telemetry.",
                logic_text=self._dsl_from_signal(signal, cycle_id=cycle.id, index=index),
                output_text="Return: plan, execution payload, and measurable success criteria.",
                run_instructions="Collect output metrics after each run for self-iteration.",
                visibility="private",
                monetization_mode="free",
                is_premium=False,
                token_price=None,
            )
            created = await self._platform.create_blueprint(viewer=owner, body=body)

            row = await self._repo.get_blueprint_by_id(blueprint_id=created.id)
            if row is not None:
                row.autonomous_mode = True
                row.autonomous_stage = "draft"
                row.autonomous_quality_score = 0.0
                row.autonomous_target_segment = signal.key[:120]
                row.autonomous_last_iteration_at = None
                await self._repo.save_blueprint(row)
                created.autonomous_mode = True
                created.autonomous_stage = "draft"
                created.autonomous_target_segment = row.autonomous_target_segment
                created.autonomous_quality_score = 0.0
            generated.append(created)

        return generated, [self._signal_to_read(item) for item in selected]

class ExperimentOrchestrator:
    def __init__(
        self,
        *,
        repo: ScenarioPlatformRepository,
        platform: ScenarioPlatformService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._platform = platform
        self._settings = settings

    def _deterministic_jitter(self, seed: str) -> float:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 1601
        return (bucket / 100.0) - 8.0

    def _metric_bundle(self, *, row: UserScenarioBlueprint, signal: ScenarioAutonomyNeedSignalRead) -> tuple[dict[str, float], dict[str, float]]:
        runs = max(int(row.run_count or 0), 1)
        completion = (float(row.completion_count or 0) / float(runs)) * 100.0 if row.run_count else 35.0
        completion = min(max(completion, 5.0), 99.0)
        retention = min(95.0, max(8.0, completion * 0.72 + float(row.save_count or 0) * 0.35))
        revenue = max(1.0, float(row.token_price or 0) * 0.4 + float(row.run_count or 0) * 0.2 + 5.0)

        jitter = self._deterministic_jitter(f"{row.id}:{signal.key}")
        conversion_lift = signal.strength * 16.0 + jitter
        retention_lift = signal.strength * 10.0 + (jitter / 2.0)
        revenue_lift = signal.strength * 12.0 + max(jitter, -3.0)

        baseline = {
            "conversion": round(completion, 2),
            "retention": round(retention, 2),
            "revenue": round(revenue, 2),
        }
        treatment = {
            "conversion": round(min(99.0, max(0.0, completion + conversion_lift)), 2),
            "retention": round(min(99.0, max(0.0, retention + retention_lift)), 2),
            "revenue": round(max(0.0, revenue + revenue_lift), 2),
        }
        return baseline, treatment

    async def _create_experiment(
        self,
        *,
        cycle_id: uuid.UUID,
        blueprint_id: uuid.UUID,
        experiment_key: str,
        dimension: str,
        control_variant: str,
        treatment_variant: str,
        baseline_metrics: dict[str, float],
        outcome_metrics: dict[str, float],
        winner_variant: str,
        now: datetime,
    ) -> ScenarioAutonomyExperiment:
        row = ScenarioAutonomyExperiment(
            cycle_id=cycle_id,
            blueprint_id=blueprint_id,
            experiment_key=experiment_key,
            dimension=dimension,
            status="completed",
            control_variant=control_variant,
            treatment_variant=treatment_variant,
            winner_variant=winner_variant,
            baseline_metrics_json=baseline_metrics,
            outcome_metrics_json=outcome_metrics,
            created_at=now,
            completed_at=now,
        )
        return await self._repo.create_autonomy_experiment(row)

    async def orchestrate(
        self,
        *,
        owner: User,
        cycle: ScenarioAutonomyCycle,
        blueprint: ScenarioBlueprintRead,
        signal: ScenarioAutonomyNeedSignalRead,
    ) -> tuple[bool, int, list[ScenarioAutonomyExperimentRead], list[ScenarioAutonomyGuardrailRead]]:
        now = datetime.now(timezone.utc)
        row = await self._repo.get_blueprint_by_id(blueprint_id=blueprint.id)
        if row is None:
            return False, 0, [], []

        baseline, treatment = self._metric_bundle(row=row, signal=signal)
        min_improvement = float(self._settings.scenario_autonomy_min_improvement_percent)
        retention_floor = float(self._settings.scenario_autonomy_guardrail_min_retention_percent)

        conversion_gain = treatment["conversion"] - baseline["conversion"]
        retention_ok = treatment["retention"] >= retention_floor
        winner = "treatment" if conversion_gain >= min_improvement and retention_ok else "control"

        experiments: list[ScenarioAutonomyExperiment] = []
        guardrails: list[ScenarioAutonomyGuardrailEvent] = []

        experiments.append(
            await self._create_experiment(
                cycle_id=cycle.id,
                blueprint_id=row.id,
                experiment_key=f"scenario_variant:{row.slug}",
                dimension="scenario",
                control_variant="control_dsl",
                treatment_variant="optimized_dsl",
                baseline_metrics=baseline,
                outcome_metrics=treatment,
                winner_variant=winner,
                now=now,
            )
        )

        ui_variant = "guided" if winner == "treatment" else "control"
        pricing_variant = "operator_pack" if treatment["revenue"] > baseline["revenue"] else "standard"
        paywall_variant = "value_focused" if winner == "treatment" else "soft"

        for dimension, treatment_variant in (
            ("ui", ui_variant),
            ("pricing", pricing_variant),
            ("paywall", paywall_variant),
        ):
            experiments.append(
                await self._create_experiment(
                    cycle_id=cycle.id,
                    blueprint_id=row.id,
                    experiment_key=f"{dimension}_variant:{row.slug}",
                    dimension=dimension,
                    control_variant="control",
                    treatment_variant=treatment_variant,
                    baseline_metrics=baseline,
                    outcome_metrics=treatment,
                    winner_variant="treatment" if winner == "treatment" else "control",
                    now=now,
                )
            )

        if not retention_ok:
            guardrails.append(
                await self._repo.create_autonomy_guardrail_event(
                    ScenarioAutonomyGuardrailEvent(
                        cycle_id=cycle.id,
                        scope="scenario",
                        rule_key="min_retention",
                        severity="critical",
                        triggered=True,
                        details_json={
                            "retention_floor": retention_floor,
                            "treatment_retention": treatment["retention"],
                            "blueprint_id": str(row.id),
                        },
                        created_at=now,
                    )
                )
            )
            row.autonomous_stage = "rolled_back"
            row.autonomous_quality_score = _score_blueprint(row)
            await self._repo.save_blueprint(row)
        else:
            iterations = 0
            if winner == "treatment":
                existing_metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
                autonomous_meta = existing_metadata.get("autonomous") if isinstance(existing_metadata.get("autonomous"), dict) else {}
                autonomous_meta.update(
                    {
                        "last_iteration_at": now.isoformat(),
                        "winner": winner,
                        "conversion_gain": round(conversion_gain, 2),
                    }
                )
                existing_metadata["autonomous"] = autonomous_meta
                await self._platform.patch_blueprint(
                    viewer=owner,
                    blueprint_id=row.id,
                    body=ScenarioBlueprintPatchWrite(
                        logic_text=(row.logic_text or "")
                        + "\n\n# v5.autonomous_iteration\n- apply_winner_variant: true\n- monitor_guardrails: true",
                        metadata=existing_metadata,
                    ),
                )
                iterations = 1
            if not row.is_published:
                await self._platform.publish_blueprint(viewer=owner, blueprint_id=row.id)
            updated = await self._repo.get_blueprint_by_id(blueprint_id=row.id)
            if updated is not None:
                updated.autonomous_mode = True
                updated.autonomous_stage = "published"
                updated.autonomous_quality_score = _score_blueprint(updated)
                updated.autonomous_last_iteration_at = now if winner == "treatment" else updated.autonomous_last_iteration_at
                await self._repo.save_blueprint(updated)
            return True, iterations, [self._to_experiment_read(item) for item in experiments], [
                self._to_guardrail_read(item) for item in guardrails
            ]

        return False, 0, [self._to_experiment_read(item) for item in experiments], [
            self._to_guardrail_read(item) for item in guardrails
        ]

    def _to_experiment_read(self, row: ScenarioAutonomyExperiment) -> ScenarioAutonomyExperimentRead:
        return ScenarioAutonomyExperimentRead(
            id=row.id,
            cycle_id=row.cycle_id,
            blueprint_id=row.blueprint_id,
            experiment_key=row.experiment_key,
            dimension=row.dimension,  # type: ignore[arg-type]
            status=row.status,
            control_variant=row.control_variant,
            treatment_variant=row.treatment_variant,
            winner_variant=row.winner_variant,
            baseline_metrics=row.baseline_metrics_json if isinstance(row.baseline_metrics_json, dict) else {},
            outcome_metrics=row.outcome_metrics_json if isinstance(row.outcome_metrics_json, dict) else {},
            created_at=row.created_at,
            completed_at=row.completed_at,
        )

    def _to_guardrail_read(self, row: ScenarioAutonomyGuardrailEvent) -> ScenarioAutonomyGuardrailRead:
        return ScenarioAutonomyGuardrailRead(
            id=row.id,
            cycle_id=row.cycle_id,
            scope=row.scope,  # type: ignore[arg-type]
            rule_key=row.rule_key,
            severity=row.severity,  # type: ignore[arg-type]
            triggered=bool(row.triggered),
            details=row.details_json if isinstance(row.details_json, dict) else {},
            created_at=row.created_at,
        )

class GrowthDecisionEngine:
    def __init__(
        self,
        *,
        repo: ScenarioPlatformRepository,
        analytics_repo: AnalyticsRepository,
        billing_repo: BillingRepository,
        analytics: AnalyticsService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._analytics_repo = analytics_repo
        self._billing_repo = billing_repo
        self._analytics = analytics
        self._settings = settings

    def _percent(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)

    async def evaluate(self, *, cycle: ScenarioAutonomyCycle) -> tuple[list[ScenarioAutonomyGrowthDecisionRead], list[ScenarioAutonomyGuardrailRead]]:
        now = datetime.now(timezone.utc)
        from_ts = now - timedelta(days=max(7, int(self._settings.scenario_autonomy_signal_window_days)))

        rows = await self._analytics_repo.list_event_rows_with_dims(
            from_ts=from_ts,
            to_ts=now,
            event_names=[
                AnalyticsEventName.signup_completed.value,
                AnalyticsEventName.scenario_run.value,
                AnalyticsEventName.scenario_resumed.value,
                AnalyticsEventName.scenario_completed.value,
                AnalyticsEventName.subscription_activated.value,
                AnalyticsEventName.paywall_viewed.value,
                AnalyticsEventName.paywall_interaction.value,
                AnalyticsEventName.pricing_plan_selected.value,
                AnalyticsEventName.checkout_started.value,
            ],
            user_only=False,
        )

        user_ids = {user_id for user_id, _session, _event, _at, _meta, _s, _m, _c, _ad, _cr in rows if user_id is not None}
        attributions = await self._analytics_repo.list_user_attributions(user_ids=list(user_ids))
        source_by_user = {
            str(item.user_id): ((item.first_utm_source or item.last_utm_source or "direct").strip().lower() or "direct")
            for item in attributions
        }

        spend_rows = await self._analytics_repo.list_channel_spend_rows(day_from=from_ts.date(), day_to=now.date())
        subscriptions = await self._billing_repo.list_subscriptions(statuses=_ACTIVE_SUB_STATUSES)

        metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "signups": set(),
                "activated": set(),
                "paid": set(),
                "retained": set(),
                "spend": 0.0,
                "revenue": 0.0,
            }
        )

        paywall_views = 0
        paywall_interactions = 0
        pricing_checks = 0
        checkouts = 0

        for user_id, _session_id, event_name, occurred_at, _metadata, utm_source, _utm_medium, _utm_campaign, _ad_id, _creative_id in rows:
            source = ((utm_source or "").strip().lower() or "direct")
            if user_id is not None:
                source = source_by_user.get(str(user_id), source)
                user_key = str(user_id)
            else:
                user_key = None

            bucket = metrics[source]
            if event_name == AnalyticsEventName.signup_completed.value and user_key:
                bucket["signups"].add(user_key)
            if event_name in {AnalyticsEventName.scenario_run.value, AnalyticsEventName.scenario_completed.value} and user_key:
                bucket["activated"].add(user_key)
            if event_name == AnalyticsEventName.subscription_activated.value and user_key:
                bucket["paid"].add(user_key)
            if event_name in {AnalyticsEventName.scenario_resumed.value, AnalyticsEventName.scenario_completed.value} and user_key:
                if occurred_at >= now - timedelta(days=7):
                    bucket["retained"].add(user_key)

            if event_name == AnalyticsEventName.paywall_viewed.value:
                paywall_views += 1
            if event_name == AnalyticsEventName.paywall_interaction.value:
                paywall_interactions += 1
            if event_name == AnalyticsEventName.pricing_plan_selected.value:
                pricing_checks += 1
            if event_name == AnalyticsEventName.checkout_started.value:
                checkouts += 1

        for item in spend_rows:
            source = (item.source or "direct").strip().lower() or "direct"
            metrics[source]["spend"] += float(item.cost_usd_cents or 0) / 100.0

        for sub in subscriptions:
            source = source_by_user.get(str(sub.user_id), "direct")
            price = float(sub.plan.price_usd_month if sub.plan is not None else 0)
            metrics[source]["revenue"] += price
            metrics[source]["paid"].add(str(sub.user_id))

        decisions: list[ScenarioAutonomyGrowthDecisionRead] = []
        guardrails: list[ScenarioAutonomyGuardrailRead] = []

        max_cac = float(self._settings.scenario_autonomy_guardrail_max_cac_usd)
        min_roi = float(self._settings.scenario_autonomy_guardrail_min_roi_percent)
        min_retention = float(self._settings.scenario_autonomy_guardrail_min_retention_percent)

        for source, values in metrics.items():
            paid = len(values["paid"])
            activated = len(values["activated"])
            signups = len(values["signups"])
            retained = len(values["retained"])
            spend = round(float(values["spend"]), 2)
            revenue = round(float(values["revenue"]), 2)

            cac = round(spend / paid, 2) if spend > 0 and paid > 0 else None
            roi = round(((revenue - spend) / spend) * 100.0, 2) if spend > 0 else 0.0
            retention = self._percent(retained, max(1, paid if paid > 0 else activated))
            conversion = self._percent(paid, max(1, activated if activated > 0 else signups))

            action = "adjust_budget"
            delta = 5.0
            if paid >= 2 and roi >= 20.0 and retention >= min_retention:
                action = "scale_channel"
                delta = 25.0
            elif spend >= 50.0 and ((roi < min_roi) or (cac is not None and cac > max_cac)):
                action = "kill_channel"
                delta = -100.0
            elif roi < 0:
                action = "adjust_budget"
                delta = -15.0
            else:
                action = "adjust_budget"
                delta = 10.0

            guardrail_passed = True
            if action == "scale_channel" and cac is not None and cac > max_cac:
                guardrail_passed = False
                action = "adjust_budget"
                delta = 0.0
                guardrail = await self._repo.create_autonomy_guardrail_event(
                    ScenarioAutonomyGuardrailEvent(
                        cycle_id=cycle.id,
                        scope="growth",
                        rule_key="max_cac",
                        severity="critical",
                        triggered=True,
                        details_json={
                            "source": source,
                            "cac": cac,
                            "max_cac": max_cac,
                        },
                        created_at=now,
                    )
                )
                guardrails.append(
                    ScenarioAutonomyGuardrailRead(
                        id=guardrail.id,
                        cycle_id=guardrail.cycle_id,
                        scope=guardrail.scope,  # type: ignore[arg-type]
                        rule_key=guardrail.rule_key,
                        severity=guardrail.severity,  # type: ignore[arg-type]
                        triggered=bool(guardrail.triggered),
                        details=guardrail.details_json if isinstance(guardrail.details_json, dict) else {},
                        created_at=guardrail.created_at,
                    )
                )

            decision = await self._repo.create_autonomy_growth_decision(
                ScenarioAutonomyGrowthDecision(
                    cycle_id=cycle.id,
                    source=source,
                    campaign=None,
                    action=action,
                    rationale_json={
                        "roi": roi,
                        "cac": cac,
                        "retention": retention,
                        "conversion": conversion,
                    },
                    before_state_json={
                        "budget_usd": spend,
                    },
                    after_state_json={
                        "budget_delta_percent": delta,
                    },
                    guardrail_passed=guardrail_passed,
                    created_at=now,
                )
            )
            decisions.append(
                ScenarioAutonomyGrowthDecisionRead(
                    id=decision.id,
                    cycle_id=decision.cycle_id,
                    source=decision.source,
                    campaign=decision.campaign,
                    action=decision.action,  # type: ignore[arg-type]
                    rationale=decision.rationale_json if isinstance(decision.rationale_json, dict) else {},
                    before_state=decision.before_state_json if isinstance(decision.before_state_json, dict) else {},
                    after_state=decision.after_state_json if isinstance(decision.after_state_json, dict) else {},
                    guardrail_passed=bool(decision.guardrail_passed),
                    created_at=decision.created_at,
                )
            )

            event_name: AnalyticsEventName | None = None
            if action == "scale_channel":
                event_name = AnalyticsEventName.scale_channel
            elif action == "kill_channel":
                event_name = AnalyticsEventName.kill_channel
            elif action == "adjust_budget":
                event_name = AnalyticsEventName.adjust_budget

            if event_name is not None:
                await self._analytics.record_server_event(
                    event_name=event_name,
                    user_id=None,
                    event_id=f"{event_name.value}:{source}:{now.date().isoformat()}",
                    metadata={
                        "source": source,
                        "roi": roi,
                        "cac": cac,
                        "retention": retention,
                        "conversion": conversion,
                        "budget_delta_percent": delta,
                    },
                    context_page="/api/v1/scenarios/autonomy/run",
                    context_feature="growth_decision_engine",
                )

        if paywall_views > 0 and paywall_interactions / max(paywall_views, 1) < 0.2:
            decision = await self._repo.create_autonomy_growth_decision(
                ScenarioAutonomyGrowthDecision(
                    cycle_id=cycle.id,
                    source="global",
                    campaign=None,
                    action="adjust_paywall",
                    rationale_json={
                        "paywall_views": paywall_views,
                        "paywall_interactions": paywall_interactions,
                        "interaction_rate": round(paywall_interactions / max(paywall_views, 1), 4),
                    },
                    before_state_json={"paywall_variant": "soft"},
                    after_state_json={"paywall_variant": "value_focused"},
                    guardrail_passed=True,
                    created_at=now,
                )
            )
            decisions.append(
                ScenarioAutonomyGrowthDecisionRead(
                    id=decision.id,
                    cycle_id=decision.cycle_id,
                    source=decision.source,
                    campaign=decision.campaign,
                    action=decision.action,  # type: ignore[arg-type]
                    rationale=decision.rationale_json if isinstance(decision.rationale_json, dict) else {},
                    before_state=decision.before_state_json if isinstance(decision.before_state_json, dict) else {},
                    after_state=decision.after_state_json if isinstance(decision.after_state_json, dict) else {},
                    guardrail_passed=bool(decision.guardrail_passed),
                    created_at=decision.created_at,
                )
            )
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.adjust_paywall,
                user_id=None,
                event_id=f"adjust_paywall:{cycle.id}",
                metadata={
                    "paywall_views": paywall_views,
                    "paywall_interactions": paywall_interactions,
                },
                context_page="/api/v1/scenarios/autonomy/run",
                context_feature="growth_decision_engine",
            )

        if pricing_checks > 0 and checkouts / max(pricing_checks, 1) < 0.25:
            decision = await self._repo.create_autonomy_growth_decision(
                ScenarioAutonomyGrowthDecision(
                    cycle_id=cycle.id,
                    source="global",
                    campaign=None,
                    action="adjust_pricing",
                    rationale_json={
                        "pricing_checks": pricing_checks,
                        "checkouts": checkouts,
                        "checkout_rate": round(checkouts / max(pricing_checks, 1), 4),
                    },
                    before_state_json={"pricing_variant": "standard"},
                    after_state_json={"pricing_variant": "operator_pack"},
                    guardrail_passed=True,
                    created_at=now,
                )
            )
            decisions.append(
                ScenarioAutonomyGrowthDecisionRead(
                    id=decision.id,
                    cycle_id=decision.cycle_id,
                    source=decision.source,
                    campaign=decision.campaign,
                    action=decision.action,  # type: ignore[arg-type]
                    rationale=decision.rationale_json if isinstance(decision.rationale_json, dict) else {},
                    before_state=decision.before_state_json if isinstance(decision.before_state_json, dict) else {},
                    after_state=decision.after_state_json if isinstance(decision.after_state_json, dict) else {},
                    guardrail_passed=bool(decision.guardrail_passed),
                    created_at=decision.created_at,
                )
            )
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.adjust_pricing,
                user_id=None,
                event_id=f"adjust_pricing:{cycle.id}",
                metadata={
                    "pricing_checks": pricing_checks,
                    "checkouts": checkouts,
                },
                context_page="/api/v1/scenarios/autonomy/run",
                context_feature="growth_decision_engine",
            )

        return decisions, guardrails

class ScenarioAutonomyService:
    def __init__(
        self,
        *,
        repo: ScenarioPlatformRepository,
        platform: ScenarioPlatformService,
        analytics_repo: AnalyticsRepository,
        analytics: AnalyticsService,
        billing_repo: BillingRepository,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._platform = platform
        self._analytics_repo = analytics_repo
        self._analytics = analytics
        self._billing_repo = billing_repo
        self._settings = settings
        self._generation = ScenarioGenerationEngine(
            repo=repo,
            analytics_repo=analytics_repo,
            platform=platform,
            settings=settings,
        )
        self._experiments = ExperimentOrchestrator(
            repo=repo,
            platform=platform,
            settings=settings,
        )
        self._growth = GrowthDecisionEngine(
            repo=repo,
            analytics_repo=analytics_repo,
            billing_repo=billing_repo,
            analytics=analytics,
            settings=settings,
        )

    def _self_check(
        self,
        *,
        generated_count: int,
        experiment_count: int,
        decision_count: int,
        iteration_count: int,
    ) -> ScenarioAutonomySelfCheckRead:
        creates = generated_count > 0
        tests = experiment_count > 0
        decides = decision_count > 0
        improves = iteration_count > 0
        return ScenarioAutonomySelfCheckRead(
            creates_new_scenarios=creates,
            tests_autonomously=tests,
            makes_decisions_autonomously=decides,
            improves_without_human=improves,
            all_passed=creates and tests and decides and improves,
        )

    async def _evolve_marketplace(self, *, cycle_id: uuid.UUID) -> int:
        threshold = float(self._settings.scenario_autonomy_marketplace_prune_threshold)
        candidates = await self._repo.list_autonomous_iteration_candidates(min_runs=2, limit=200)
        retired = 0
        now = datetime.now(timezone.utc)
        for row in candidates:
            quality = _score_blueprint(row)
            row.autonomous_quality_score = quality
            row.autonomous_last_iteration_at = now
            if quality < threshold:
                row.autonomous_stage = "retired"
                retired += 1
            else:
                row.autonomous_stage = "published"
            await self._repo.save_blueprint(row)

        await self._repo.create_autonomy_guardrail_event(
            ScenarioAutonomyGuardrailEvent(
                cycle_id=cycle_id,
                scope="marketplace",
                rule_key="prune_low_quality",
                severity="info",
                triggered=retired > 0,
                details_json={
                    "retired_count": retired,
                    "quality_threshold": threshold,
                },
                created_at=now,
            )
        )
        return retired

    async def _to_cycle_read(
        self,
        cycle: ScenarioAutonomyCycle,
        *,
        signals: list[ScenarioAutonomyNeedSignalRead] | None = None,
    ) -> ScenarioAutonomyCycleRead:
        experiments = [
            ScenarioAutonomyExperimentRead(
                id=row.id,
                cycle_id=row.cycle_id,
                blueprint_id=row.blueprint_id,
                experiment_key=row.experiment_key,
                dimension=row.dimension,  # type: ignore[arg-type]
                status=row.status,
                control_variant=row.control_variant,
                treatment_variant=row.treatment_variant,
                winner_variant=row.winner_variant,
                baseline_metrics=row.baseline_metrics_json if isinstance(row.baseline_metrics_json, dict) else {},
                outcome_metrics=row.outcome_metrics_json if isinstance(row.outcome_metrics_json, dict) else {},
                created_at=row.created_at,
                completed_at=row.completed_at,
            )
            for row in await self._repo.list_autonomy_experiments(cycle_id=cycle.id)
        ]
        growth_decisions = [
            ScenarioAutonomyGrowthDecisionRead(
                id=row.id,
                cycle_id=row.cycle_id,
                source=row.source,
                campaign=row.campaign,
                action=row.action,  # type: ignore[arg-type]
                rationale=row.rationale_json if isinstance(row.rationale_json, dict) else {},
                before_state=row.before_state_json if isinstance(row.before_state_json, dict) else {},
                after_state=row.after_state_json if isinstance(row.after_state_json, dict) else {},
                guardrail_passed=bool(row.guardrail_passed),
                created_at=row.created_at,
            )
            for row in await self._repo.list_autonomy_growth_decisions(cycle_id=cycle.id)
        ]
        guardrails = [
            ScenarioAutonomyGuardrailRead(
                id=row.id,
                cycle_id=row.cycle_id,
                scope=row.scope,  # type: ignore[arg-type]
                rule_key=row.rule_key,
                severity=row.severity,  # type: ignore[arg-type]
                triggered=bool(row.triggered),
                details=row.details_json if isinstance(row.details_json, dict) else {},
                created_at=row.created_at,
            )
            for row in await self._repo.list_autonomy_guardrail_events(cycle_id=cycle.id)
        ]
        if signals is None:
            notes = cycle.notes_json if isinstance(cycle.notes_json, dict) else {}
            raw_signals = notes.get("signals") if isinstance(notes.get("signals"), list) else []
            signals = []
            for item in raw_signals:
                if not isinstance(item, dict):
                    continue
                try:
                    signals.append(ScenarioAutonomyNeedSignalRead.model_validate(item))
                except Exception:
                    continue

        self_check = self._self_check(
            generated_count=int(cycle.generated_count or 0),
            experiment_count=len(experiments),
            decision_count=len(growth_decisions),
            iteration_count=int(cycle.iterations_count or 0),
        )
        return ScenarioAutonomyCycleRead(
            id=cycle.id,
            trigger=cycle.trigger,
            status=cycle.status,
            started_at=cycle.started_at,
            finished_at=cycle.finished_at,
            generated_count=int(cycle.generated_count or 0),
            published_count=int(cycle.published_count or 0),
            iterations_count=int(cycle.iterations_count or 0),
            signals=signals,
            experiments=experiments,
            growth_decisions=growth_decisions,
            guardrails=guardrails,
            self_check=self_check,
        )

    async def run_autonomous_cycle(
        self,
        *,
        actor: User | None,
        trigger: str = "manual",
        max_new_scenarios: int | None = None,
        force: bool = False,
    ) -> ScenarioAutonomyCycleRead:
        if not self._settings.scenario_autonomy_enabled:
            raise AppError(
                code="scenario_autonomy_disabled",
                message="Autonomous scenario system is disabled in runtime settings.",
                status_code=409,
            )

        now = datetime.now(timezone.utc)
        latest = await self._repo.get_latest_autonomy_cycle()
        if (
            not force
            and latest is not None
            and latest.finished_at is not None
            and (now - latest.finished_at) < timedelta(minutes=3)
        ):
            return await self._to_cycle_read(latest)

        cycle = await self._repo.create_autonomy_cycle(
            ScenarioAutonomyCycle(
                trigger=trigger,
                status="running",
                started_at=now,
                finished_at=None,
                generated_count=0,
                published_count=0,
                iterations_count=0,
                notes_json={},
                created_at=now,
            )
        )

        try:
            preferred_user_id = actor.id if actor is not None else None
            owner = await self._repo.resolve_autonomous_owner(preferred_user_id=preferred_user_id)
            if owner is None:
                cycle.status = "skipped"
                cycle.finished_at = datetime.now(timezone.utc)
                cycle.notes_json = {"reason": "no_users"}
                await self._repo.save_autonomy_cycle(cycle)
                return await self._to_cycle_read(cycle)

            configured_limit = max(1, int(self._settings.scenario_autonomy_max_new_scenarios_per_cycle))
            effective_limit = max_new_scenarios if max_new_scenarios is not None else configured_limit
            if trigger == "manual" and actor is not None and actor.id != owner.id:
                effective_limit = min(1, effective_limit)

            generated, signals = await self._generation.generate(
                owner=owner,
                cycle=cycle,
                max_scenarios=max(1, effective_limit),
            )

            published_count = 0
            iterations_count = 0
            signal_map = {item.key: item for item in signals}

            for blueprint in generated:
                signal = signal_map.get(blueprint.autonomous_target_segment or "")
                if signal is None and signals:
                    signal = signals[0]
                if signal is None:
                    continue
                published, iterations, _exp, _guard = await self._experiments.orchestrate(
                    owner=owner,
                    cycle=cycle,
                    blueprint=blueprint,
                    signal=signal,
                )
                if published:
                    published_count += 1
                iterations_count += iterations

            growth_decisions, growth_guardrails = await self._growth.evaluate(cycle=cycle)
            retired_count = await self._evolve_marketplace(cycle_id=cycle.id)

            cycle.generated_count = len(generated)
            cycle.published_count = int(published_count)
            cycle.iterations_count = int(iterations_count)
            cycle.status = "completed"
            cycle.finished_at = datetime.now(timezone.utc)
            cycle.notes_json = {
                "signals": [item.model_dump() for item in signals],
                "growth_decision_count": len(growth_decisions),
                "growth_guardrail_count": len(growth_guardrails),
                "retired_count": retired_count,
                "owner_user_id": str(owner.id),
            }
            await self._repo.save_autonomy_cycle(cycle)

            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.autonomous_cycle_completed,
                user_id=owner.id,
                event_id=f"autonomy_cycle_completed:{cycle.id}",
                metadata={
                    "cycle_id": str(cycle.id),
                    "generated_count": cycle.generated_count,
                    "published_count": cycle.published_count,
                    "iterations_count": cycle.iterations_count,
                    "growth_decision_count": len(growth_decisions),
                },
                context_page="/api/v1/scenarios/autonomy/run",
                context_feature="scenario_autonomy_service",
            )

            return await self._to_cycle_read(cycle, signals=signals)
        except Exception as exc:
            cycle.status = "failed"
            cycle.finished_at = datetime.now(timezone.utc)
            cycle.notes_json = {
                "error": exc.__class__.__name__,
                "message": str(exc),
            }
            await self._repo.save_autonomy_cycle(cycle)
            raise

    async def get_status(self) -> ScenarioAutonomyStatusRead:
        latest = await self._repo.get_latest_autonomy_cycle()
        total_cycles = await self._repo.count_autonomy_cycles()
        latest_read = await self._to_cycle_read(latest) if latest is not None else None

        if latest_read is not None:
            self_check = latest_read.self_check
        else:
            self_check = ScenarioAutonomySelfCheckRead(
                creates_new_scenarios=False,
                tests_autonomously=False,
                makes_decisions_autonomously=False,
                improves_without_human=False,
                all_passed=False,
            )

        return ScenarioAutonomyStatusRead(
            enabled=bool(self._settings.scenario_autonomy_enabled),
            scheduler_enabled=bool(self._settings.scenario_autonomy_scheduler_enabled),
            latest_cycle=latest_read,
            total_cycles=total_cycles,
            self_check=self_check,
        )

    async def get_self_check(self) -> ScenarioAutonomySelfCheckRead:
        status = await self.get_status()
        return status.self_check

    async def _refresh_personalization_profile(self, *, viewer: User) -> ScenarioAutonomyPersonalizationProfile:
        my_blueprints = await self._repo.list_owner_blueprints(owner_user_id=viewer.id)
        categories = [item.category for item in my_blueprints if item.category]
        if not categories:
            autonomous_rows = await self._repo.list_autonomous_blueprints(only_published=True, limit=60)
            categories = [item.category for item in autonomous_rows if item.category]

        top_categories: list[str] = []
        for category, _count in Counter(categories).most_common(3):
            if category and category not in top_categories:
                top_categories.append(category)
        if not top_categories:
            top_categories = ["utility", "productivity"]

        latest_cycle = await self._repo.get_latest_autonomy_cycle()
        ui_variant = "control"
        paywall_variant = "soft"
        pricing_variant = "standard"
        if latest_cycle is not None:
            experiments = await self._repo.list_autonomy_experiments(cycle_id=latest_cycle.id)
            for row in experiments:
                if row.dimension == "ui" and row.winner_variant == "treatment":
                    ui_variant = row.treatment_variant
                if row.dimension == "paywall" and row.winner_variant == "treatment":
                    paywall_variant = row.treatment_variant
                if row.dimension == "pricing" and row.winner_variant == "treatment":
                    pricing_variant = row.treatment_variant

        recommended: list[ScenarioBlueprintRead] = []
        used_ids: set[uuid.UUID] = set()
        for category in top_categories:
            rows = await self._platform.list_marketplace_blueprints(
                limit=8,
                section="personalized",
                category=category,
                viewer=viewer,
            )
            for item in rows:
                if item.id in used_ids:
                    continue
                recommended.append(item)
                used_ids.add(item.id)
                if len(recommended) >= 10:
                    break
            if len(recommended) >= 10:
                break

        profile = await self._repo.get_personalization_profile(user_id=viewer.id)
        now = datetime.now(timezone.utc)
        if profile is None:
            profile = await self._repo.create_personalization_profile(
                ScenarioAutonomyPersonalizationProfile(
                    user_id=viewer.id,
                    ui_variant=ui_variant,
                    paywall_variant=paywall_variant,
                    pricing_variant=pricing_variant,
                    preferred_categories=top_categories,
                    recommended_blueprint_ids=[str(item.id) for item in recommended],
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            profile.ui_variant = ui_variant
            profile.paywall_variant = paywall_variant
            profile.pricing_variant = pricing_variant
            profile.preferred_categories = top_categories
            profile.recommended_blueprint_ids = [str(item.id) for item in recommended]
            profile.updated_at = now
            profile = await self._repo.save_personalization_profile(profile)
        return profile

    async def get_personalization(
        self,
        *,
        viewer: User,
    ) -> ScenarioAutonomyPersonalizationRead:
        profile = await self._repo.get_personalization_profile(user_id=viewer.id)
        now = datetime.now(timezone.utc)
        if profile is None or (now - profile.updated_at) > timedelta(hours=6):
            profile = await self._refresh_personalization_profile(viewer=viewer)

        ids: list[uuid.UUID] = []
        for raw_id in profile.recommended_blueprint_ids:
            try:
                ids.append(uuid.UUID(str(raw_id)))
            except Exception:
                continue

        recommended_rows = await self._repo.list_blueprints_by_ids(ids)
        by_id = {item.id: item for item in recommended_rows}
        recommended: list[ScenarioBlueprintRead] = []
        for item_id in ids:
            row = by_id.get(item_id)
            if row is None:
                continue
            if bool(getattr(row, "autonomous_mode", False)) and str(getattr(row, "autonomous_stage", "manual")) == "retired":
                continue
            recommended.append(
                ScenarioBlueprintRead(
                    id=row.id,
                    owner_user_id=row.owner_user_id,
                    slug=row.slug,
                    title=row.title,
                    summary=row.summary,
                    category=row.category,
                    tags=list(row.tags or []),
                    metadata=row.metadata_json if isinstance(row.metadata_json, dict) else None,
                    author_display_name=None,
                    visibility=row.visibility,
                    monetization_mode=row.monetization_mode,
                    autonomous_mode=bool(getattr(row, "autonomous_mode", False)),
                    autonomous_stage=str(getattr(row, "autonomous_stage", "manual") or "manual"),
                    autonomous_quality_score=float(getattr(row, "autonomous_quality_score", 0.0) or 0.0),
                    autonomous_target_segment=getattr(row, "autonomous_target_segment", None),
                    autonomous_last_iteration_at=getattr(row, "autonomous_last_iteration_at", None),
                    is_published=bool(row.is_published),
                    is_premium=bool(row.is_premium),
                    token_price=row.token_price,
                    input_schema=row.input_schema,
                    context_text=row.context_text,
                    logic_text=row.logic_text,
                    output_text=row.output_text,
                    run_instructions=row.run_instructions,
                    usage_count=int(row.usage_count or 0),
                    run_count=int(row.run_count or 0),
                    completion_count=int(row.completion_count or 0),
                    save_count=int(row.save_count or 0),
                    fork_count=int(row.fork_count or 0),
                    like_count=int(row.like_count or 0),
                    comment_count=int(row.comment_count or 0),
                    rating_average=float(row.rating_average or 0.0),
                    rating_count=int(row.rating_count or 0),
                    version_number=int(row.version_number or 1),
                    forked_from_id=row.forked_from_id,
                    root_blueprint_id=row.root_blueprint_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    published_at=row.published_at,
                )
            )

        reasons = [
            "Category affinity from your scenario history.",
            "Autonomous experiment winners currently active.",
            "Low-friction path to next high-value action.",
        ]
        return ScenarioAutonomyPersonalizationRead(
            user_id=viewer.id,
            ui_variant=profile.ui_variant,
            paywall_variant=profile.paywall_variant,
            pricing_variant=profile.pricing_variant,
            preferred_categories=list(profile.preferred_categories or []),
            reasons=reasons,
            recommended_blueprints=recommended[:8],
            updated_at=profile.updated_at,
        )
