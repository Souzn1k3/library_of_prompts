from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.infrastructure.db.models import LessonMission, User, UserMissionProgress, UserMissionStepProgress
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.analytics_emitter import MissionAnalyticsEmitter
from app.modules.missions.service.event_matcher import MissionEventMatcher
from app.modules.missions.service.mission_event_mixin import MissionEventMixin
from app.modules.missions.service.mission_read_mixin import MissionReadMixin
from app.modules.missions.service.policy import MissionPolicy
from app.modules.missions.service.reward_planner import MissionRewardPlanner
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository


class MissionService(MissionReadMixin, MissionEventMixin):
    def __init__(
        self,
        repo: MissionRepository,
        onboarding_repo: OnboardingRepository,
        prompt_repo: PromptRepository,
        wallet_repo: WalletRepository | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._onboarding = onboarding_repo
        self._prompts = prompt_repo
        self._wallet_repo = wallet_repo
        self._policy = MissionPolicy()
        self._reward_planner = MissionRewardPlanner(wallet_repo)
        self._analytics = analytics
        self._event_matcher = MissionEventMatcher()
        self._analytics_emitter = MissionAnalyticsEmitter(
            analytics=analytics,
            wallet_repo=wallet_repo,
        )

    async def _build_reward_plan(
        self,
        *,
        user: User,
        mission: LessonMission,
        event_type: str,
        base_credits: int,
        source_key: str,
        include_chain_bonus: bool,
        segment: str,
        now: datetime,
    ) -> dict[str, Any]:
        return await self._reward_planner.build_reward_plan(
            user=user,
            mission=mission,
            event_type=event_type,
            base_credits=base_credits,
            source_key=source_key,
            include_chain_bonus=include_chain_bonus,
            segment=segment,
            now=now,
        )

    async def _grant_reward_extras(
        self,
        *,
        user: User,
        mission: LessonMission,
        source_id: uuid.UUID,
        cycle_number: int,
        now: datetime,
        source_context: str,
        plan: dict[str, Any],
    ) -> int:
        return await self._reward_planner.grant_reward_extras(
            user=user,
            mission=mission,
            source_id=source_id,
            cycle_number=cycle_number,
            now=now,
            source_context=source_context,
            plan=plan,
        )

    async def _reset_progress_cycle_if_needed(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        now: datetime,
    ) -> None:
        if progress is None or not self._policy.can_reset_cycle(mission, progress, now=now):
            return
        await self._repo.reset_progress_cycle(
            progress=progress,
            step_progress_rows=[step_progress[step.id] for step in mission.steps if step.id in step_progress],
        )
