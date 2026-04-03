import uuid
from hashlib import sha256
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
    ANTI_FARM_BREAKPOINTS,
    ANTI_FARM_FALLBACK_FACTOR,
    MISSION_DAILY_EARN_CAP,
    MISSION_REWARD_EVENT_COOLDOWN,
    STREAK_SURPRISE_HIT_CHANCE_PERCENT,
    STREAK_SURPRISE_PITY_THRESHOLD,
)
from app.modules.economy.service.experiment_service import economy_experiment_metadata
from app.modules.economy.service.wallet_service import WalletService
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
        self._wallet = WalletService(wallet_repo) if wallet_repo else None
        self._analytics = analytics

    def _is_eligible(
        self,
        mission: LessonMission,
        profile: OnboardingProfile | None,
        *,
        segment: str = "balanced",
    ) -> bool:
        adaptive_segment = (mission.adaptive_segment or "").strip().lower()
        if adaptive_segment and adaptive_segment not in {"any", segment}:
            return False
        if profile is None:
            return mission.persona_role is None and mission.persona_goal is None
        if mission.persona_role is not None and profile.role != mission.persona_role:
            return False
        if mission.persona_goal is not None and profile.goal != mission.persona_goal:
            return False
        return True

    def _persona_score(
        self,
        mission: LessonMission,
        profile: OnboardingProfile | None,
        *,
        segment: str = "balanced",
    ) -> int:
        if profile is None:
            base = 1 if mission.persona_role is None and mission.persona_goal is None else 0
        else:
            base = 0
            if mission.persona_role is None:
                base += 1
            elif profile.role == mission.persona_role:
                base += 3
            if mission.persona_goal is None:
                base += 1
            elif profile.goal == mission.persona_goal:
                base += 3

        adaptive_segment = (mission.adaptive_segment or "").strip().lower()
        if adaptive_segment and adaptive_segment == segment:
            base += 2
        return base

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

    def _available_again_at(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
    ) -> datetime | None:
        if (
            progress is None
            or progress.completed_at is None
            or not mission.is_repeatable
            or mission.repeat_interval_days <= 0
        ):
            return None
        completed_at = (
            progress.completed_at
            if progress.completed_at.tzinfo is not None
            else progress.completed_at.replace(tzinfo=timezone.utc)
        )
        return completed_at + timedelta(days=mission.repeat_interval_days)

    def _can_reset_cycle(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        now: datetime,
    ) -> bool:
        available_again_at = self._available_again_at(mission, progress)
        return bool(available_again_at is not None and available_again_at <= now)

    def _required_step_count(self, step: MissionStep) -> int:
        return max(1, step.required_count)

    def _required_mission_count(self, mission: LessonMission) -> int:
        return max(1, mission.required_count) if not mission.steps else sum(
            self._required_step_count(step) for step in mission.steps
        )

    def _step_progress_totals(self, mission: LessonMission, step_progress: dict[uuid.UUID, UserMissionStepProgress]) -> tuple[int, int]:
        total_required = total_progress = 0
        for step in mission.steps:
            required = self._required_step_count(step)
            row = step_progress.get(step.id)
            total_required += required
            total_progress += min(row.progress_count if row else 0, required)
        return total_required, min(total_required, total_progress)

    def _mission_category(self, mission: LessonMission, *, event_type: str) -> str:
        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
            MissionActionType.apply_prompt,
        }:
            return "prompt"
        if mission.action_type == MissionActionType.lesson_completed:
            return "learning"
        if mission.action_type in {
            MissionActionType.daily_checkin,
            MissionActionType.streak_activity,
        }:
            return "habit"
        if mission.action_type == MissionActionType.store_purchase or event_type == "store_purchase":
            return "spend"
        return "progress"

    def _anti_farm_factor(self, same_day_count: int) -> float:
        for threshold, factor in ANTI_FARM_BREAKPOINTS:
            if same_day_count <= threshold:
                return factor
        return ANTI_FARM_FALLBACK_FACTOR

    def _day_bounds(self, now: datetime) -> tuple[datetime, datetime]:
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return start, start + timedelta(days=1)

    def _daily_cap_for_rank(self, rank_level: int) -> int:
        allowance = min(10, max(0, rank_level - 1))
        return MISSION_DAILY_EARN_CAP + allowance

    def _surprise_hit(self, *, seed: str, pity_count: int) -> bool:
        if pity_count >= STREAK_SURPRISE_PITY_THRESHOLD:
            return True
        digest = int(sha256(seed.encode("utf-8")).hexdigest(), 16)
        return digest % 100 < STREAK_SURPRISE_HIT_CHANCE_PERCENT

    def _is_chain_unlocked(
        self,
        mission: LessonMission,
        *,
        mission_by_slug: dict[str, LessonMission],
        progress_map: dict[uuid.UUID, UserMissionProgress],
    ) -> bool:
        unlock_slug = (mission.chain_unlock_on_slug or "").strip()
        if not unlock_slug:
            return True
        unlock_mission = mission_by_slug.get(unlock_slug)
        if unlock_mission is None:
            return True
        progress = progress_map.get(unlock_mission.id)
        if progress is None:
            return False
        return progress.completed_at is not None or progress.status == MissionProgressStatus.completed

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
        base_credits = max(0, int(base_credits))
        if self._wallet_repo is None or base_credits <= 0:
            return {
                "base_reward": base_credits,
                "spend_bonus": 0,
                "chain_bonus": 0,
                "surprise_bonus": 0,
                "components": {
                    "base_credits": base_credits,
                    "anti_farm_factor": 1.0,
                    "synergy_bonus": 0,
                    "boost_mult": 1.0,
                    "catchup_mult": 1.0,
                    "catchup_boost_pct": 0,
                    "catchup_activated": False,
                    "spend_streak_mult": 1.0,
                    "daily_cap": MISSION_DAILY_EARN_CAP,
                    "daily_earned_before": 0,
                    "daily_earned_available": MISSION_DAILY_EARN_CAP,
                    "owned_value_delta": 0,
                },
            }

        day_start, day_end = self._day_bounds(now)
        same_day_count = await self._wallet_repo.count_mission_events_since(
            user_id=user.id,
            mission_id=mission.id,
            since=day_start,
        )
        anti_farm_factor = self._anti_farm_factor(same_day_count)
        mission_category = self._mission_category(mission, event_type=event_type)
        synergy_bonus = await self._wallet_repo.owned_synergy_bonus(
            user_id=user.id,
            mission_category=mission_category,
        )
        balance_row = await self._wallet_repo.get_balance_row(user.id, for_update=True)
        spend_streak_mult = self._wallet_repo.spend_streak_multiplier(int(balance_row.spend_streak_days))
        catchup_mult, catchup_boost_pct, catchup_activated = await self._wallet_repo.resolve_catchup_boost(
            user_id=user.id,
            segment=segment,
            now=now,
        )
        boost_mult, boost_pct, boost_missions_left = await self._wallet_repo.consume_active_boost(
            user_id=user.id,
            now=now,
        )
        total_boost_mult = boost_mult * catchup_mult

        pity_count = int(balance_row.surprise_miss_streak)
        surprise_seed = f"{source_key}:{mission.slug}:{base_credits}:{same_day_count}"
        surprise_hit = self._surprise_hit(seed=surprise_seed, pity_count=pity_count)
        surprise_roll_bonus = 0
        if surprise_hit:
            surprise_roll_bonus = 2 + min(4, max(0, int(balance_row.rank_level) - 1) // 2)
            balance_row.surprise_miss_streak = 0
        else:
            balance_row.surprise_miss_streak = pity_count + 1

        chain_bonus = int(mission.chain_bonus_credits) if include_chain_bonus else 0
        base_component = max(0, int(base_credits * anti_farm_factor + synergy_bonus))
        boosted_component = max(0, int(base_component * total_boost_mult))
        spend_bonus_component = max(0, int(boosted_component * max(spend_streak_mult - 1.0, 0.0)))
        composed_total = boosted_component + spend_bonus_component + chain_bonus + surprise_roll_bonus

        catchup_only_component = max(0, int(base_component * catchup_mult))
        owned_boost_delta = max(0, boosted_component - catchup_only_component)
        owned_value_delta = max(0, int(synergy_bonus)) + owned_boost_delta
        if owned_value_delta > 0:
            balance_row.owned_value_generated = int(balance_row.owned_value_generated) + owned_value_delta

        daily_cap = self._daily_cap_for_rank(int(balance_row.rank_level))
        earned_today_before = await self._wallet_repo.sum_mission_earnings_today(
            user_id=user.id,
            start_of_day=day_start,
            end_of_day=day_end,
        )
        available_today = max(0, daily_cap - earned_today_before)
        capped_total = min(composed_total, available_today)

        remaining = capped_total
        base_reward = min(boosted_component, remaining)
        remaining -= base_reward
        spend_bonus = min(spend_bonus_component, remaining)
        remaining -= spend_bonus
        chain_award = min(chain_bonus, remaining)
        remaining -= chain_award
        surprise_award = max(0, remaining)

        return {
            "base_reward": max(0, base_reward),
            "spend_bonus": max(0, spend_bonus),
            "chain_bonus": max(0, chain_award),
            "surprise_bonus": max(0, surprise_award),
            "components": {
                "base_credits": base_credits,
                "anti_farm_factor": anti_farm_factor,
                "same_day_count": same_day_count,
                "mission_category": mission_category,
                "synergy_bonus": synergy_bonus,
                "boost_mult": round(boost_mult, 4),
                "boost_pct": boost_pct,
                "boost_missions_left": boost_missions_left,
                "catchup_mult": round(catchup_mult, 4),
                "catchup_boost_pct": catchup_boost_pct,
                "catchup_activated": catchup_activated,
                "spend_streak_mult": round(spend_streak_mult, 4),
                "daily_cap": daily_cap,
                "daily_earned_before": earned_today_before,
                "daily_earned_available": available_today,
                "pre_cap_total": composed_total,
                "post_cap_total": capped_total,
                "pity_before": pity_count,
                "surprise_hit": surprise_hit,
                "surprise_roll_bonus": surprise_roll_bonus,
                "chain_bonus_configured": chain_bonus,
                "owned_value_delta": owned_value_delta,
            },
        }

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
        if self._wallet_repo is None:
            return int(plan.get("base_reward", 0) or 0)

        total_awarded = int(plan.get("base_reward", 0) or 0)
        components = dict(plan.get("components") or {})
        for key, reason in (
            ("spend_bonus", CurrencyTransactionType.spend_streak_bonus),
            ("chain_bonus", CurrencyTransactionType.rank_bonus),
            ("surprise_bonus", CurrencyTransactionType.surprise_reward),
        ):
            amount = int(plan.get(key, 0) or 0)
            if amount <= 0:
                continue
            total_awarded += amount
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=amount,
                reason=reason,
                context=f"{source_context}:{key}:cycle:{cycle_number}",
                source_id=source_id,
                metadata={
                    "mission_id": str(mission.id),
                    "mission_slug": mission.slug,
                    "reward_cycle": cycle_number,
                    "reward_component": key,
                    **components,
                },
                now=now,
            )
        return total_awarded

    async def _reset_progress_cycle_if_needed(self, mission: LessonMission, progress: UserMissionProgress | None, *, step_progress: dict[uuid.UUID, UserMissionStepProgress], now: datetime) -> None:
        if progress is None or not self._can_reset_cycle(mission, progress, now=now):
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
        required_count = progress.required_count if progress else self._required_step_count(step)

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
        available_again_at = self._available_again_at(mission, progress)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else self._required_mission_count(mission)

        steps: list[MissionStepRead] = []
        if mission.steps:
            steps = [
                self._step_read(step, step_progress=step_progress, user=user, can_view_premium=can_view_premium)
                for step in mission.steps
            ]
            required_count, progress_count = self._step_progress_totals(mission, step_progress)
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
            if self._is_eligible(mission, profile, segment=segment)
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
            if self._is_chain_unlocked(
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
                -self._persona_score(mission, profile, segment=segment),
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

    def _matches_event(
        self,
        mission: LessonMission,
        *,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        step: MissionStep | None = None,
    ) -> bool:
        action_type = step.action_type if step else mission.action_type
        linked_prompt_ids = (
            {step.target_prompt_id} if step and step.target_prompt_id else {link.prompt_id for link in mission.prompt_links}
        )
        if action_type == MissionActionType.copy_prompt:
            if event_type != "prompt_copied":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.save_prompt:
            if event_type != "prompt_saved":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.copy_or_save_prompt:
            if event_type not in {"prompt_copied", "prompt_saved"}:
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.apply_prompt:
            if event_type != "prompt_applied":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.lesson_completed:
            if event_type != "lesson_completed":
                return False
            lesson_target = step.target_lesson_id if step else mission.lesson_id
            if lesson_target and lesson_id != lesson_target:
                return False
            return lesson_id is not None
        if action_type == MissionActionType.onboarding_first_win:
            return event_type == "onboarding_first_win_completed"
        if action_type == MissionActionType.manual_confirmation:
            return event_type == "mission_manual_confirmed"
        if action_type == MissionActionType.daily_checkin:
            return event_type == "daily_checkin"
        if action_type == MissionActionType.streak_activity:
            return event_type in {"streak_activity", "daily_checkin"}
        if action_type == MissionActionType.challenge_submission:
            return event_type == "challenge_submitted"
        if action_type == MissionActionType.store_purchase:
            return event_type == "store_purchase"
        if action_type == MissionActionType.multi_step:
            # Steps handle this action; if no steps, allow generic completion event
            return event_type in {"mission_manual_confirmed", "mission_step_completed"}
        return False

    def _matching_target_steps(self, mission: LessonMission, *, event_type: str, prompt_id: uuid.UUID | None, lesson_id: uuid.UUID | None) -> list[MissionStep | None]:
        if mission.steps:
            return [
                step
                for step in mission.steps
                if self._matches_event(
                    mission,
                    event_type=event_type,
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                    step=step,
                )
            ]
        if self._matches_event(
            mission,
            event_type=event_type,
            prompt_id=prompt_id,
            lesson_id=lesson_id,
        ):
            return [None]
        return []

    async def _ensure_progress(self, *, user_id: uuid.UUID, mission: LessonMission, progress_map: dict[uuid.UUID, UserMissionProgress]) -> UserMissionProgress:
        progress = progress_map.get(mission.id)
        if progress is not None:
            return progress
        progress = await self._repo.create_progress(UserMissionProgress(user_id=user_id, mission_id=mission.id, required_count=self._required_mission_count(mission), status=MissionProgressStatus.not_started, progress_count=0))
        progress_map[mission.id] = progress
        return progress

    async def _ensure_step_progress(self, *, user_id: uuid.UUID, step: MissionStep | None, step_progress_map: dict[uuid.UUID, UserMissionStepProgress]) -> UserMissionStepProgress | None:
        if step is None:
            return None
        step_progress = step_progress_map.get(step.id)
        if step_progress is not None:
            return step_progress
        step_progress = await self._repo.create_step_progress(UserMissionStepProgress(user_id=user_id, mission_step_id=step.id, required_count=self._required_step_count(step), status=MissionProgressStatus.not_started, progress_count=0))
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
            if self._is_eligible(mission, profile, segment=segment)
        ]
        mission_slug_by_id = {mission.id: mission.slug for mission in eligible}

        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}
        completed_slugs: list[str] = []

        for mission in eligible:
            await self._reset_progress_cycle_if_needed(mission, progress_map.get(mission.id), step_progress=step_progress_map, now=now)
            if not self._is_chain_unlocked(
                mission,
                mission_by_slug=mission_by_slug,
                progress_map=progress_map,
            ):
                continue
            target_steps = self._matching_target_steps(mission, event_type=event_type, prompt_id=prompt_id, lesson_id=lesson_id)
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
                    progress.required_count, progress.progress_count = self._step_progress_totals(mission, step_progress_map)

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
                await self._emit_mission_analytics(
                    user=user,
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

    async def _emit_mission_analytics(
        self,
        *,
        user: User,
        mission: LessonMission,
        mission_slug: str,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        source_event_key: str,
        mission_step_id: uuid.UUID | None,
        progress: UserMissionProgress,
        cycle_number: int,
        started_now: bool,
        completed_now: bool,
    ) -> None:
        if self._analytics is None:
            return

        payer_status = "non_payer"
        if self._wallet_repo is not None:
            _, _, total_spent = await self._wallet_repo.summary(user.id)
            payer_status = "payer" if int(total_spent) > 0 else "non_payer"

        base_metadata = {
            "mission_id": str(mission.id),
            "mission_slug": mission_slug,
            "mission_action_type": mission.action_type.value,
            "source_event_key": source_event_key,
            "mission_cycle": cycle_number,
            "trigger_event_type": event_type,
            "progress_count": progress.progress_count,
            "required_count": progress.required_count,
            "prompt_id": str(prompt_id) if prompt_id is not None else None,
            "lesson_id": str(lesson_id) if lesson_id is not None else None,
            "mission_step_id": str(mission_step_id) if mission_step_id is not None else None,
            **economy_experiment_metadata(user_id=user.id, payer_status=payer_status),
        }

        if started_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_started,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_started:{user.id}:{mission.id}:cycle:{cycle_number}",
            )

        if not completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_progressed,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=(
                    f"mission_progressed:{user.id}:{mission.id}:cycle:{cycle_number}:"
                    f"{progress.progress_count}:{source_event_key}"
                ),
            )

        if completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_completed,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_completed:{user.id}:{mission.id}:cycle:{cycle_number}",
            )
            if mission.slug == STREAK_RECOVERY_MISSION_SLUG:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.streak_recovery_completed,
                    user_id=user.id,
                    metadata=base_metadata,
                    context_page="/api/v1/missions/events",
                    context_feature="streak_recovery",
                    event_id=f"streak_recovery_completed:{user.id}:{mission.id}:cycle:{cycle_number}",
                )

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
