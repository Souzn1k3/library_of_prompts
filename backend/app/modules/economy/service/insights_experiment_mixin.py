from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.modules.economy.model.insights import EconomyExperimentKpiRead, EconomyGuardrailRead
from app.modules.economy.service.experiment_service import ECONOMY_EXPERIMENT_NAME, economy_experiment_variant


class EconomyInsightsExperimentMixin:
    async def experiment_kpis(self, *, window_days: int = 14) -> EconomyExperimentKpiRead:
        now = datetime.now(timezone.utc)
        start_at = now - timedelta(days=max(1, window_days))
        end_at = now
        end_date = now.date()

        purchases = await self._repo.list_purchases(start_at=start_at, end_at=end_at)
        mission_events = await self._repo.list_mission_events(start_at=start_at, end_at=end_at)
        tx_rows = await self._repo.list_currency_transactions(start_at=start_at, end_at=end_at)
        wallet_rows_raw = await self._repo.list_wallet_rows()
        analytics_rows = await self._repo.list_analytics_events(
            start_at=start_at,
            end_at=end_at,
            event_names=[
                "store_offer_viewed",
                "store_purchase_completed",
                "goal_completed",
            ],
        )

        purchases_by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
        activity_days: dict[uuid.UUID, set[date]] = defaultdict(set)
        first_activity: dict[uuid.UUID, date] = {}
        for user_id, created_at in purchases:
            purchases_by_user[user_id].append(created_at)
            day = created_at.astimezone(timezone.utc).date()
            activity_days[user_id].add(day)
            first_activity[user_id] = min(first_activity.get(user_id, day), day)
        for user_id, created_at in mission_events:
            day = created_at.astimezone(timezone.utc).date()
            activity_days[user_id].add(day)
            first_activity[user_id] = min(first_activity.get(user_id, day), day)

        tx_by_user: dict[uuid.UUID, list[tuple[int, str]]] = defaultdict(list)
        for user_id, amount, reason, _created_at in tx_rows:
            tx_by_user[user_id].append((amount, reason))

        wallet_rows: dict[uuid.UUID, tuple[int, int, int, int]] = {}
        payer_status_by_user: dict[uuid.UUID, str] = {}
        for user_id, current_streak, balance, rank_level, total_spent in wallet_rows_raw:
            wallet_rows[user_id] = (current_streak, balance, rank_level, total_spent)
            payer_status_by_user[user_id] = "payer" if total_spent > 0 else "non_payer"

        offer_views_by_user: dict[uuid.UUID, int] = defaultdict(int)
        offer_conversions_by_user: dict[uuid.UUID, int] = defaultdict(int)
        goals_completed_users: set[uuid.UUID] = set()
        for user_id, event_name, metadata, _occurred_at in analytics_rows:
            if user_id is None:
                continue
            if event_name == "store_offer_viewed":
                offer_views_by_user[user_id] += 1
            elif event_name == "store_purchase_completed":
                if bool((metadata or {}).get("is_limited_offer")) or bool((metadata or {}).get("is_dynamic_offer")):
                    offer_conversions_by_user[user_id] += 1
            elif event_name == "goal_completed":
                goals_completed_users.add(user_id)

        active_users = set(activity_days.keys()) | set(purchases_by_user.keys()) | set(tx_by_user.keys())
        variant_users: dict[str, set[uuid.UUID]] = {"control": set(), "treatment": set()}
        for user_id in active_users:
            payer_status = payer_status_by_user.get(user_id, "non_payer")
            variant = economy_experiment_variant(user_id=user_id, payer_status=payer_status)
            variant_users[variant].add(user_id)

        arms = []
        for variant in ("control", "treatment"):
            metrics = self._arm_kpis(
                users=variant_users.get(variant, set()),
                purchases_by_user=purchases_by_user,
                activity_days=activity_days,
                first_activity=first_activity,
                tx_by_user=tx_by_user,
                offer_views_by_user=offer_views_by_user,
                offer_conversions_by_user=offer_conversions_by_user,
                goals_completed_users=goals_completed_users,
                wallet_rows=wallet_rows,
                end_date=end_date,
            )
            metrics.variant = variant
            arms.append(metrics)

        control = next((arm for arm in arms if arm.variant == "control"), None)
        treatment = next((arm for arm in arms if arm.variant == "treatment"), None)
        retention_drop_flag = bool(
            control and treatment and (treatment.d7_retention + 0.03) < control.d7_retention
        )
        inflation_breach_flag = bool(treatment and treatment.lmn_circulation_ratio < 0.45)

        mission_events_per_user: dict[str, float] = {}
        for variant, users in variant_users.items():
            if not users:
                mission_events_per_user[variant] = 0.0
                continue
            mission_count = len([1 for user_id, _created_at in mission_events if user_id in users])
            mission_events_per_user[variant] = mission_count / len(users)
        mission_completion_collapse_flag = (
            mission_events_per_user.get("control", 0.0) > 0
            and mission_events_per_user.get("treatment", 0.0)
            < (mission_events_per_user.get("control", 0.0) * 0.8)
        )
        decision_ready = bool(
            window_days >= 14
            and control is not None
            and treatment is not None
            and control.users >= 50
            and treatment.users >= 50
        )
        guardrails_pass = not any(
            (
                retention_drop_flag,
                inflation_breach_flag,
                mission_completion_collapse_flag,
            )
        )
        if not decision_ready:
            next_step = "continue_ab_test_until_minimum_runtime"
        elif guardrails_pass:
            next_step = "pass_guardrails_stage_ramp_50_to_100"
        else:
            next_step = "hold_rollout_and_tune_economy"

        return EconomyExperimentKpiRead(
            experiment_name=ECONOMY_EXPERIMENT_NAME,
            generated_at=now,
            window_days=window_days,
            arms=arms,
            guardrails=EconomyGuardrailRead(
                retention_drop_flag=retention_drop_flag,
                inflation_breach_flag=inflation_breach_flag,
                mission_completion_collapse_flag=mission_completion_collapse_flag,
            ),
            is_decision_ready=decision_ready,
            recommended_next_step=next_step,
        )
