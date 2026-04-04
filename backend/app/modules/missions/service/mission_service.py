import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.errors import AppError, NotFoundError
from app.core.tiers import can_view_lesson, can_view_premium_content, can_view_restricted_category
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LessonMission,
    MissionActionType,
    MissionStep,
    MissionProgressStatus,
    OnboardingProfile,
    PromptStatus,
    User,
    UserMissionProgress,
    UserMissionStepProgress,
)
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.config.tuning import (
    MISSION_REWARD_EVENT_COOLDOWN,
)
from app.modules.economy.service.experiment_service import economy_experiment_metadata
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.model.prompt import PromptSort
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.missions.model.mission import (
    MissionCurrentRead,
    MissionLessonRef,
    MissionListRead,
    MissionNextStep,
    MissionPromptRef,
    MissionRead,
    MissionRewardSummary,
    MissionRewardView,
    MissionStepRead,
)
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.analytics_emitter import MissionAnalyticsEmitter
from app.modules.missions.service.event_matcher import MissionEventMatcher
from app.modules.missions.service.policy import MissionPolicy
from app.modules.missions.service.reward_planner import MissionRewardPlanner
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.persona_hints import build_persona_hint_query


COOLDOWN_EVENT_TYPES = {"prompt_copied", "prompt_saved", "prompt_applied", "daily_checkin", "streak_activity"}
STREAK_RECOVERY_MISSION_SLUG = "streak-recovery-window"


class MissionService:
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

    def _mission_next_step(
        self,
        mission: LessonMission,
        *,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
        status: MissionProgressStatus,
        step_progress: dict[uuid.UUID, UserMissionStepProgress] | None = None,
    ) -> MissionNextStep | None:
        if mission.steps:
            step_progress = step_progress or {}
            pending = next(
                (s for s in mission.steps if step_progress.get(s.id, None) is None or step_progress[s.id].status != MissionProgressStatus.completed),
                None,
            )
            if pending:
                if pending.target_prompt:
                    return MissionNextStep(
                        label=f"Try: {pending.title}",
                        href=f"/prompt/{pending.target_prompt.slug}",
                        action="open_step_prompt",
                    )
                if pending.target_lesson:
                    return MissionNextStep(
                        label=f"Open lesson: {pending.title}",
                        href=f"/learn/{pending.target_lesson.slug}",
                        action="open_step_lesson",
                    )
                return MissionNextStep(label=f"Next step: {pending.title}", href=f"/missions/{mission.slug}", action="view_step")

        if status == MissionProgressStatus.completed:
            return MissionNextStep(
                label="View result",
                href=f"/missions/{mission.slug}",
                action="view_result",
            )

        if mission.action_type == MissionActionType.onboarding_first_win:
            return MissionNextStep(label="Complete first win", href="/onboarding", action="finish_onboarding")

        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
        }:
            if prompts:
                return MissionNextStep(
                    label="Try linked prompt",
                    href=f"/prompt/{prompts[0].slug}",
                    action="open_prompt",
                )
            return MissionNextStep(label="Browse catalog", href="/catalog", action="browse_prompts")

        if mission.action_type == MissionActionType.lesson_completed:
            if lesson and lesson.locked:
                return MissionNextStep(
                    label="Unlock lesson",
                    href=f"/plans?tier={lesson.min_tier.value}",
                    action="upgrade_for_lesson",
                )
            if lesson:
                return MissionNextStep(
                    label="Continue lesson",
                    href=f"/learn/{lesson.slug}",
                    action="open_lesson",
                )
            return MissionNextStep(label="Browse lessons", href="/learn", action="browse_lessons")

        return MissionNextStep(label="Open mission details", href=f"/missions/{mission.slug}", action="details")


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

    async def _reset_progress_cycle_if_needed(self, mission: LessonMission, progress: UserMissionProgress | None, *, step_progress: dict[uuid.UUID, UserMissionStepProgress], now: datetime) -> None:
        if progress is None or not self._policy.can_reset_cycle(mission, progress, now=now):
            return
        await self._repo.reset_progress_cycle(progress=progress, step_progress_rows=[step_progress[step.id] for step in mission.steps if step.id in step_progress])

    async def _fallback_prompts(self, user: User, profile: OnboardingProfile | None) -> list[MissionPromptRef]:
        role = profile.role.value if profile and profile.role else "other"
        goal = profile.goal.value if profile and profile.goal else "learning"
        query = build_persona_hint_query(role=role, goal=goal)
        rows = await self._prompts.list_published(
            skip=0,
            limit=3,
            q=query,
            sort=PromptSort.relevance,
            restrict_to_unrestricted_categories=not can_view_restricted_category(user),
            only_free=not can_view_premium_content(user),
        )
        out: list[MissionPromptRef] = []
        for row in rows:
            if row.status != PromptStatus.published:
                continue
            out.append(MissionPromptRef(id=row.id, slug=row.slug, title=row.title, summary=row.summary))
        return out

    def _mission_prompts(
        self,
        mission: LessonMission,
        *,
        can_view_premium: bool,
        fallback_prompts: list[MissionPromptRef],
    ) -> list[MissionPromptRef]:
        linked: list[MissionPromptRef] = []
        for link in sorted(mission.prompt_links, key=lambda row: row.sort_order):
            prompt = link.prompt
            if prompt is None or prompt.status != PromptStatus.published:
                continue
            if prompt.is_premium and not can_view_premium:
                continue
            linked.append(
                MissionPromptRef(
                    id=prompt.id,
                    slug=prompt.slug,
                    title=prompt.title,
                    summary=prompt.summary,
                )
            )
        return linked if linked else fallback_prompts

    def _step_read(
        self,
        step: MissionStep,
        *,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        user: User,
        can_view_premium: bool,
    ) -> MissionStepRead:
        progress = step_progress.get(step.id)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else self._policy.required_step_count(step)

        prompt = None
        if step.target_prompt:
            target_prompt = step.target_prompt
            if not target_prompt.is_premium or can_view_premium:
                prompt = MissionPromptRef(
                    id=target_prompt.id,
                    slug=target_prompt.slug,
                    title=target_prompt.title,
                    summary=target_prompt.summary,
                )

        lesson = None
        if step.target_lesson:
            target_lesson = step.target_lesson
            lesson = MissionLessonRef(id=target_lesson.id, slug=target_lesson.slug, title=target_lesson.title, min_tier=target_lesson.min_tier, locked=not can_view_lesson(user, target_lesson.min_tier))

        return MissionStepRead(
            id=step.id,
            title=step.title,
            description=step.description,
            action_type=step.action_type,
            status=status,
            progress_count=progress_count,
            required_count=required_count,
            reward_credits=step.reward_credits,
            prompt=prompt,
            lesson=lesson,
        )

    def _synergy_preview_for_mission(self, mission: LessonMission) -> int:
        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
            MissionActionType.apply_prompt,
            MissionActionType.lesson_completed,
            MissionActionType.store_purchase,
        }:
            return 1
        return 0

    def _mission_read(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        user: User,
        segment: str,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        can_view_premium: bool,
    ) -> MissionRead:
        available_again_at = self._policy.available_again_at(mission, progress)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else self._policy.required_mission_count(mission)

        steps: list[MissionStepRead] = []
        if mission.steps:
            steps = [
                self._step_read(step, step_progress=step_progress, user=user, can_view_premium=can_view_premium)
                for step in mission.steps
            ]
            required_count, progress_count = self._policy.step_progress_totals(mission, step_progress)
            if progress_count >= required_count and required_count > 0:
                status = MissionProgressStatus.completed
        reward = MissionRewardView(
            badge=mission.reward_badge,
            credits=mission.reward_credits,
            premium_days=mission.reward_premium_days,
            granted_at=progress.reward_granted_at if progress else None,
        )
        next_step = self._mission_next_step(
            mission,
            prompts=prompts,
            lesson=lesson,
            status=status,
            step_progress=step_progress,
        )
        return MissionRead(
            id=mission.id,
            slug=mission.slug,
            title=mission.title,
            description=mission.description,
            objective=mission.objective,
            completion_condition=mission.completion_condition,
            difficulty=mission.difficulty,
            mission_type=mission.mission_type,
            action_type=mission.action_type,
            is_repeatable=mission.is_repeatable,
            repeat_interval_days=mission.repeat_interval_days,
            chain_id=mission.chain_id,
            chain_step=int(mission.chain_step),
            chain_total=int(mission.chain_total),
            chain_next_unlocked=bool(
                mission.chain_id
                and int(mission.chain_total) > 0
                and int(mission.chain_step) < int(mission.chain_total)
                and status == MissionProgressStatus.completed
            ),
            adaptive_reason=(
                "streak_recovery_window"
                if mission.slug == STREAK_RECOVERY_MISSION_SLUG
                else (mission.adaptive_segment or segment)
            ),
            synergy_bonus_preview=self._synergy_preview_for_mission(mission),
            status=status,
            completion_count=progress.completion_count if progress else 0,
            progress_count=min(progress_count, required_count),
            required_count=required_count,
            started_at=progress.started_at if progress else None,
            last_event_at=progress.last_event_at if progress else None,
            completed_at=progress.completed_at if progress else None,
            available_again_at=available_again_at,
            prompts=prompts,
            lesson=lesson,
            steps=steps,
            reward=reward,
            next_step=next_step,
        )

    async def _build_missions(self, user: User) -> tuple[list[MissionRead], MissionRewardSummary]:
        now = datetime.now(timezone.utc)
        profile = await self._onboarding.get_profile(user.id)
        segment = (
            await self._wallet_repo.classify_user_segment(user_id=user.id, now=now)
            if self._wallet_repo is not None
            else "balanced"
        )
        can_view_premium = can_view_premium_content(user)
        fallback_prompts = await self._fallback_prompts(user, profile)

        all_missions = await self._repo.list_active_missions()
        mission_by_slug = {mission.slug: mission for mission in all_missions}
        eligible = [
            mission
            for mission in all_missions
            if self._policy.is_eligible(mission, profile, segment=segment)
        ]
        should_offer_recovery = (
            await self._wallet_repo.should_offer_streak_recovery(user_id=user.id, now=now)
            if self._wallet_repo is not None
            else False
        )
        if should_offer_recovery and self._analytics is not None:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.streak_recovery_offered,
                user_id=user.id,
                metadata={"offered_at": now.isoformat()},
                context_page="/api/v1/missions",
                context_feature="streak_recovery",
                event_id=f"streak_recovery_offered:{user.id}:{now.date().isoformat()}",
            )
        eligible = [
            mission
            for mission in eligible
            if mission.slug != STREAK_RECOVERY_MISSION_SLUG or should_offer_recovery
        ]
        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}

        for mission in eligible:
            await self._reset_progress_cycle_if_needed(
                mission,
                progress_map.get(mission.id),
                step_progress=step_progress_map,
                now=now,
            )
        eligible = [
            mission
            for mission in eligible
            if self._policy.is_chain_unlocked(
                mission,
                mission_by_slug=mission_by_slug,
                progress_map=progress_map,
            )
        ]

        def sort_key(mission: LessonMission) -> tuple[int, int, int, str]:
            progress = progress_map.get(mission.id)
            if progress and progress.status == MissionProgressStatus.in_progress:
                progress_rank = 0
            elif progress and progress.status == MissionProgressStatus.not_started:
                progress_rank = 1
            elif progress is None:
                progress_rank = 1
            else:
                progress_rank = 2
            return (
                progress_rank,
                -self._policy.persona_score(mission, profile, segment=segment),
                mission.sort_order,
                mission.slug,
            )

        ordered = sorted(eligible, key=sort_key)
        mission_views: list[MissionRead] = []
        for mission in ordered:
            progress = progress_map.get(mission.id)
            prompts = self._mission_prompts(mission, can_view_premium=can_view_premium, fallback_prompts=fallback_prompts)
            lesson_ref: MissionLessonRef | None = None
            if mission.lesson is not None:
                lesson_ref = MissionLessonRef(id=mission.lesson.id, slug=mission.lesson.slug, title=mission.lesson.title, min_tier=mission.lesson.min_tier, locked=not can_view_lesson(user, mission.lesson.min_tier))
            mission_views.append(
                self._mission_read(
                    mission,
                    progress,
                    user=user,
                    segment=segment,
                    prompts=prompts,
                    lesson=lesson_ref,
                    step_progress=step_progress_map,
                    can_view_premium=can_view_premium,
                )
            )

        credits, badges, premium_unlock_until = await self._repo.get_reward_summary(user.id)
        if self._wallet_repo is not None:
            wallet_balance, _, _ = await self._wallet_repo.summary(user.id)
            credits = wallet_balance
        rewards = MissionRewardSummary(
            credits=credits,
            badges=badges,
            premium_unlock_until=premium_unlock_until,
        )
        return mission_views, rewards

    async def list_user_missions(self, user: User) -> MissionListRead:
        items, rewards = await self._build_missions(user)
        completed = [mission for mission in items if mission.status == MissionProgressStatus.completed]
        current = next((mission for mission in items if mission.status == MissionProgressStatus.in_progress), None)
        if current is None:
            current = next((mission for mission in items if mission.status != MissionProgressStatus.completed), None)
        return MissionListRead(
            missions=items,
            current_mission_slug=current.slug if current else None,
            completed_count=len(completed),
            total_count=len(items),
            rewards=rewards,
        )

    async def current_user_mission(self, user: User) -> MissionCurrentRead:
        items, rewards = await self._build_missions(user)
        current = next((mission for mission in items if mission.status == MissionProgressStatus.in_progress), None)
        if current is None:
            current = next((mission for mission in items if mission.status != MissionProgressStatus.completed), None)

        next_mission = None
        latest_completed = None
        if current is not None:
            for mission in items:
                if mission.slug == current.slug:
                    continue
                if mission.status != MissionProgressStatus.completed:
                    next_mission = mission
                    break

        completed_sorted = sorted(
            [mission for mission in items if mission.completed_at is not None],
            key=lambda row: row.completed_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        if completed_sorted:
            latest_completed = completed_sorted[0]

        completed_count = len([mission for mission in items if mission.status == MissionProgressStatus.completed])
        return MissionCurrentRead(
            current=current,
            next=next_mission,
            latest_completed=latest_completed,
            completed_count=completed_count,
            total_count=len(items),
            rewards=rewards,
        )

    async def get_mission_by_slug(self, user: User, slug: str) -> MissionRead:
        listing = await self.list_user_missions(user)
        for mission in listing.missions:
            if mission.slug == slug:
                return mission
        raise NotFoundError("mission", slug)

    async def _ensure_progress(self, *, user_id: uuid.UUID, mission: LessonMission, progress_map: dict[uuid.UUID, UserMissionProgress]) -> UserMissionProgress:
        progress = progress_map.get(mission.id)
        if progress is not None:
            return progress
        progress = await self._repo.create_progress(UserMissionProgress(user_id=user_id, mission_id=mission.id, required_count=self._policy.required_mission_count(mission), status=MissionProgressStatus.not_started, progress_count=0))
        progress_map[mission.id] = progress
        return progress

    async def _ensure_step_progress(self, *, user_id: uuid.UUID, step: MissionStep | None, step_progress_map: dict[uuid.UUID, UserMissionStepProgress]) -> UserMissionStepProgress | None:
        if step is None:
            return None
        step_progress = step_progress_map.get(step.id)
        if step_progress is not None:
            return step_progress
        step_progress = await self._repo.create_step_progress(UserMissionStepProgress(user_id=user_id, mission_step_id=step.id, required_count=self._policy.required_step_count(step), status=MissionProgressStatus.not_started, progress_count=0))
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

    async def record_event(
        self,
        *,
        user: User,
        event_type: str,
        prompt_id: uuid.UUID | None = None,
        lesson_id: uuid.UUID | None = None,
        source_event_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[str]:
        now = datetime.now(timezone.utc)
        profile = await self._onboarding.get_profile(user.id)
        segment = (
            await self._wallet_repo.classify_user_segment(user_id=user.id, now=now)
            if self._wallet_repo is not None
            else "balanced"
        )
        missions = await self._repo.list_active_missions()
        mission_by_slug = {mission.slug: mission for mission in missions}
        eligible = [
            mission
            for mission in missions
            if self._policy.is_eligible(mission, profile, segment=segment)
        ]
        mission_slug_by_id = {mission.id: mission.slug for mission in eligible}

        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}
        completed_slugs: list[str] = []

        for mission in eligible:
            await self._reset_progress_cycle_if_needed(mission, progress_map.get(mission.id), step_progress=step_progress_map, now=now)
            if not self._policy.is_chain_unlocked(
                mission,
                mission_by_slug=mission_by_slug,
                progress_map=progress_map,
            ):
                continue
            target_steps = self._event_matcher.matching_target_steps(
                mission,
                event_type=event_type,
                prompt_id=prompt_id,
                lesson_id=lesson_id,
            )
            if not target_steps:
                continue

            progress = await self._ensure_progress(user_id=user.id, mission=mission, progress_map=progress_map)
            if progress.completed_at is not None:
                continue

            current_cycle = max(1, progress.completion_count + 1)

            for step in target_steps:
                step_progress = await self._ensure_step_progress(user_id=user.id, step=step, step_progress_map=step_progress_map)
                if step_progress is not None and step_progress.completed_at is not None:
                    continue

                if event_type in COOLDOWN_EVENT_TYPES and self._wallet_repo is not None:
                    if await self._wallet_repo.has_recent_mission_event(
                        user_id=user.id,
                        mission_id=mission.id,
                        event_type=event_type,
                since=now - MISSION_REWARD_EVENT_COOLDOWN,
                    ):
                        # Per-template cooldown to suppress low-effort rapid repeats.
                        continue

                scoped_key = source_event_key or f"{event_type}:{uuid.uuid4()}"
                completion_event = await self._repo.add_completion_event(
                    progress_id=progress.id,
                    user_id=user.id,
                    mission_id=mission.id,
                    mission_step_id=step.id if step is not None else None,
                    event_type=event_type,
                    source_event_key=f"{mission.id}:cycle:{current_cycle}:{scoped_key}",
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                    payload=payload,
                    created_at=now,
                )
                if completion_event is None:
                    continue

                started_now = progress.started_at is None
                if started_now:
                    progress.started_at = now
                progress.last_event_at = now
                progress.status = MissionProgressStatus.in_progress

                if step_progress is not None:
                    await self._apply_step_progress(
                        user=user,
                        mission=mission,
                        step=step,
                        step_progress=step_progress,
                        cycle_number=current_cycle,
                        event_type=event_type,
                        source_key=scoped_key,
                        segment=segment,
                        now=now,
                    )
                else:
                    progress.progress_count = min(progress.required_count, progress.progress_count + 1)

                if mission.steps:
                    progress.required_count, progress.progress_count = self._policy.step_progress_totals(mission, step_progress_map)

                completed_now = await self._finalize_progress_completion(
                    user=user,
                    mission=mission,
                    progress=progress,
                    cycle_number=current_cycle,
                    segment=segment,
                    now=now,
                )
                if completed_now:
                    completed_slugs.append(mission.slug)

                await self._repo.save_progress(progress)
                await self._analytics_emitter.emit_progress_event(
                    user_id=user.id,
                    mission=mission,
                    mission_slug=mission_slug_by_id.get(mission.id, mission.slug),
                    event_type=event_type,
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                    source_event_key=scoped_key,
                    mission_step_id=step.id if step is not None else None,
                    progress=progress,
                    cycle_number=current_cycle,
                    started_now=started_now,
                    completed_now=completed_now,
                )

        return completed_slugs

    async def confirm_manual_step(self, user: User, slug: str) -> MissionRead:
        mission = await self._repo.get_mission_by_slug(slug)
        if mission is None:
            raise NotFoundError("mission", slug)
        if mission.action_type != MissionActionType.manual_confirmation:
            raise AppError(
                code="mission_manual_confirmation_not_allowed",
                message="Mission does not support manual confirmation",
                status_code=400,
                message_key="errors.mission_manual_confirmation_not_allowed",
            )
        if mission.slug == STREAK_RECOVERY_MISSION_SLUG and self._wallet_repo is not None:
            is_available = await self._wallet_repo.should_offer_streak_recovery(user_id=user.id)
            if not is_available:
                raise AppError(
                    code="streak_recovery_unavailable",
                    message="Streak recovery is only available in the same-day recovery window.",
                    status_code=409,
                    message_key="errors.streak_recovery_unavailable",
                )
        await self.record_event(
            user=user,
            event_type="mission_manual_confirmed",
            source_event_key=f"mission_manual_confirmed:{user.id}:{mission.id}",
        )
        if mission.slug == STREAK_RECOVERY_MISSION_SLUG and self._wallet_repo is not None:
            await self._wallet_repo.record_daily_check_in(user.id)
        return await self.get_mission_by_slug(user, slug)
