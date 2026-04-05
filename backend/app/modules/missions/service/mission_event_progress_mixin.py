from __future__ import annotations

import uuid
from datetime import datetime

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LessonMission,
    MissionProgressStatus,
    MissionStep,
    User,
    UserMissionProgress,
    UserMissionStepProgress,
)
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.economy.config.tuning import MISSION_REWARD_EVENT_COOLDOWN
from app.modules.economy.service.experiment_service import economy_experiment_metadata
from app.modules.missions.service.mission_constants import COOLDOWN_EVENT_TYPES


class MissionEventProgressMixin:
    async def _ensure_progress(
        self,
        *,
        user_id: uuid.UUID,
        mission: LessonMission,
        progress_map: dict[uuid.UUID, UserMissionProgress],
    ) -> UserMissionProgress:
        progress = progress_map.get(mission.id)
        if progress is not None:
            return progress
        progress = await self._repo.create_progress(
            UserMissionProgress(
                user_id=user_id,
                mission_id=mission.id,
                required_count=self._policy.required_mission_count(mission),
                status=MissionProgressStatus.not_started,
                progress_count=0,
            )
        )
        progress_map[mission.id] = progress
        return progress

    async def _ensure_step_progress(
        self,
        *,
        user_id: uuid.UUID,
        step: MissionStep | None,
        step_progress_map: dict[uuid.UUID, UserMissionStepProgress],
    ) -> UserMissionStepProgress | None:
        if step is None:
            return None
        step_progress = step_progress_map.get(step.id)
        if step_progress is not None:
            return step_progress
        step_progress = await self._repo.create_step_progress(
            UserMissionStepProgress(
                user_id=user_id,
                mission_step_id=step.id,
                required_count=self._policy.required_step_count(step),
                status=MissionProgressStatus.not_started,
                progress_count=0,
            )
        )
        step_progress_map[step.id] = step_progress
        return step_progress

    async def _apply_step_progress(
        self,
        *,
        user: User,
        mission: LessonMission,
        step: MissionStep,
        step_progress: UserMissionStepProgress,
        cycle_number: int,
        event_type: str,
        source_key: str,
        segment: str,
        now: datetime,
    ) -> None:
        if step_progress.started_at is None:
            step_progress.started_at = now
        step_progress.last_event_at = now
        step_progress.progress_count = min(step_progress.required_count, step_progress.progress_count + 1)
        step_progress.status = MissionProgressStatus.in_progress
        if step_progress.progress_count >= step_progress.required_count and step_progress.completed_at is None:
            step_progress.status = MissionProgressStatus.completed
            step_progress.completed_at = now
            if step.reward_credits > 0 and self._wallet_repo is not None:
                plan = await self._build_reward_plan(
                    user=user,
                    mission=mission,
                    event_type=event_type,
                    base_credits=step.reward_credits,
                    source_key=source_key,
                    include_chain_bonus=False,
                    segment=segment,
                    now=now,
                )
                if int(plan.get("base_reward", 0) or 0) > 0:
                    await self._wallet_repo.adjust_balance(
                        user_id=user.id,
                        amount=int(plan["base_reward"]),
                        reason=CurrencyTransactionType.mission_reward,
                        context=f"mission_step:{mission.slug}:cycle:{cycle_number}:{step.id}",
                        source_id=step.id,
                        metadata={
                            "mission_id": str(mission.id),
                            "mission_slug": mission.slug,
                            "step_id": str(step.id),
                            "reward_cycle": cycle_number,
                            "reward_component": "base_reward",
                            **dict(plan.get("components") or {}),
                        },
                        now=now,
                    )
                await self._grant_reward_extras(
                    user=user,
                    mission=mission,
                    source_id=step.id,
                    cycle_number=cycle_number,
                    now=now,
                    source_context=f"mission_step:{mission.slug}:{step.id}",
                    plan=plan,
                )
        await self._repo.save_step_progress(step_progress)

    async def _finalize_progress_completion(
        self,
        *,
        user: User,
        mission: LessonMission,
        progress: UserMissionProgress,
        cycle_number: int,
        segment: str,
        now: datetime,
    ) -> bool:
        if progress.progress_count < progress.required_count or progress.completed_at is not None:
            return False
        progress.status = MissionProgressStatus.completed
        progress.completed_at = now
        progress.completion_count = cycle_number
        include_chain_bonus = bool(
            mission.chain_id
            and int(mission.chain_total) > 0
            and int(mission.chain_step) >= int(mission.chain_total)
        )
        reward_plan = await self._build_reward_plan(
            user=user,
            mission=mission,
            event_type=mission.action_type.value,
            base_credits=mission.reward_credits,
            source_key=f"mission_complete:{mission.slug}:{cycle_number}",
            include_chain_bonus=include_chain_bonus,
            segment=segment,
            now=now,
        )
        progress.reward_granted_at = await self._repo.grant_rewards(
            user_id=user.id,
            mission=mission,
            reward_cycle=cycle_number,
            now=now,
            wallet_repo=self._wallet_repo,
            credit_override=int(reward_plan.get("base_reward", 0) or 0),
            credit_metadata={
                "reward_component": "base_reward",
                **dict(reward_plan.get("components") or {}),
            },
        )
        extras_total = await self._grant_reward_extras(
            user=user,
            mission=mission,
            source_id=mission.id,
            cycle_number=cycle_number,
            now=now,
            source_context=f"mission:{mission.slug}",
            plan=reward_plan,
        )
        if progress.reward_granted_at is None and extras_total > 0:
            progress.reward_granted_at = now
        if self._wallet_repo is not None:
            unlocked = await self._wallet_repo.progress_locked_cashback(
                user_id=user.id,
                mission_progress=1,
                now=now,
            )
            if unlocked and self._analytics is not None:
                _, _, total_spent = await self._wallet_repo.summary(user.id)
                payer_status = "payer" if int(total_spent) > 0 else "non_payer"
                experiment_meta = economy_experiment_metadata(user_id=user.id, payer_status=payer_status)
                for row in unlocked:
                    await self._analytics.record_server_event(
                        event_name=AnalyticsEventName.locked_cashback_unlocked,
                        user_id=user.id,
                        metadata={
                            **experiment_meta,
                            "locked_reward_id": str(row.id),
                            "source_purchase_id": str(row.source_purchase_id) if row.source_purchase_id else None,
                            "unlock_amount": int(row.amount),
                        },
                        context_page="/api/v1/missions/events",
                        context_feature="cashback_unlock",
                        event_id=f"locked_cashback_unlocked:{user.id}:{row.id}",
                    )
        return True

    async def _is_event_on_cooldown(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        event_type: str,
        now: datetime,
    ) -> bool:
        if event_type not in COOLDOWN_EVENT_TYPES or self._wallet_repo is None:
            return False
        return await self._wallet_repo.has_recent_mission_event(
            user_id=user_id,
            mission_id=mission_id,
            event_type=event_type,
            since=now - MISSION_REWARD_EVENT_COOLDOWN,
        )
