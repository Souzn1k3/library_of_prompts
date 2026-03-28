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

_ROLE_HINTS: dict[str, list[str]] = {
    "student": ["study", "exam", "summary", "explain"],
    "developer": ["debug", "code", "api", "refactor"],
    "other": ["planning", "email", "workflow", "research"],
}

_GOAL_HINTS: dict[str, list[str]] = {
    "learning": ["learn", "tutorial", "practice"],
    "solving_tasks": ["solve", "task", "step-by-step", "analysis"],
    "productivity": ["productivity", "time", "organize", "checklist"],
}


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

    def _is_eligible(self, mission: LessonMission, profile: OnboardingProfile | None) -> bool:
        if profile is None:
            return mission.persona_role is None and mission.persona_goal is None
        if mission.persona_role is not None and profile.role != mission.persona_role:
            return False
        if mission.persona_goal is not None and profile.goal != mission.persona_goal:
            return False
        return True

    def _persona_score(self, mission: LessonMission, profile: OnboardingProfile | None) -> int:
        if profile is None:
            return 1 if mission.persona_role is None and mission.persona_goal is None else 0
        score = 0
        if mission.persona_role is None:
            score += 1
        elif profile.role == mission.persona_role:
            score += 3
        if mission.persona_goal is None:
            score += 1
        elif profile.goal == mission.persona_goal:
            score += 3
        return score

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

    async def _fallback_prompts(self, user: User, profile: OnboardingProfile | None) -> list[MissionPromptRef]:
        role = profile.role.value if profile and profile.role else "other"
        goal = profile.goal.value if profile and profile.goal else "learning"
        hints = [*_ROLE_HINTS.get(role, []), *_GOAL_HINTS.get(goal, [])]
        query = " ".join(dict.fromkeys(hints)).strip() or None
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
        required_count = progress.required_count if progress else max(1, step.required_count)

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
            lesson = MissionLessonRef(
                id=target_lesson.id,
                slug=target_lesson.slug,
                title=target_lesson.title,
                min_tier=target_lesson.min_tier,
                locked=not can_view_lesson(user, target_lesson.min_tier),
            )

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

    def _mission_read(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        user: User,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        can_view_premium: bool,
    ) -> MissionRead:
        available_again_at = self._available_again_at(mission, progress)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else max(1, mission.required_count)

        steps: list[MissionStepRead] = []
        if mission.steps:
            steps = [
                self._step_read(step, step_progress=step_progress, user=user, can_view_premium=can_view_premium)
                for step in mission.steps
            ]
            required_count = sum(max(1, step.required_count) for step in mission.steps)
            progress_count = sum(
                min(
                    step_progress.get(step.id).progress_count if step_progress.get(step.id) else 0,
                    max(1, step.required_count),
                )
                for step in mission.steps
            )
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
        can_view_premium = can_view_premium_content(user)
        fallback_prompts = await self._fallback_prompts(user, profile)

        all_missions = await self._repo.list_active_missions()
        eligible = [mission for mission in all_missions if self._is_eligible(mission, profile)]
        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}

        for mission in eligible:
            progress = progress_map.get(mission.id)
            if progress is None or not self._can_reset_cycle(mission, progress, now=now):
                continue
            rows = [step_progress_map[step.id] for step in mission.steps if step.id in step_progress_map]
            await self._repo.reset_progress_cycle(progress=progress, step_progress_rows=rows)

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
                -self._persona_score(mission, profile),
                mission.sort_order,
                mission.slug,
            )

        ordered = sorted(eligible, key=sort_key)
        mission_views: list[MissionRead] = []
        for mission in ordered:
            progress = progress_map.get(mission.id)
            prompts = self._mission_prompts(
                mission,
                can_view_premium=can_view_premium,
                fallback_prompts=fallback_prompts,
            )
            lesson_ref: MissionLessonRef | None = None
            if mission.lesson is not None:
                lesson_ref = MissionLessonRef(
                    id=mission.lesson.id,
                    slug=mission.lesson.slug,
                    title=mission.lesson.title,
                    min_tier=mission.lesson.min_tier,
                    locked=not can_view_lesson(user, mission.lesson.min_tier),
                )
            mission_views.append(
                self._mission_read(
                    mission,
                    progress,
                    user=user,
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
        if action_type == MissionActionType.multi_step:
            # Steps handle this action; if no steps, allow generic completion event
            return event_type in {"mission_manual_confirmed", "mission_step_completed"}
        return False

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
        missions = await self._repo.list_active_missions()
        eligible = [mission for mission in missions if self._is_eligible(mission, profile)]
        mission_slug_by_id = {mission.id: mission.slug for mission in eligible}

        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}
        completed_slugs: list[str] = []

        for mission in eligible:
            progress = progress_map.get(mission.id)
            if progress is not None and self._can_reset_cycle(mission, progress, now=now):
                rows = [step_progress_map[step.id] for step in mission.steps if step.id in step_progress_map]
                await self._repo.reset_progress_cycle(progress=progress, step_progress_rows=rows)

            if mission.steps:
                target_steps = [
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
                if not target_steps:
                    continue
            else:
                if not self._matches_event(
                    mission,
                    event_type=event_type,
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                ):
                    continue
                target_steps = [None]

            progress = progress_map.get(mission.id)
            if progress is None:
                required_total = (
                    sum(max(1, step.required_count) for step in mission.steps)
                    if mission.steps
                    else max(1, mission.required_count)
                )
                progress = await self._repo.create_progress(
                    UserMissionProgress(
                        user_id=user.id,
                        mission_id=mission.id,
                        required_count=required_total,
                        status=MissionProgressStatus.not_started,
                        progress_count=0,
                    )
                )
                progress_map[mission.id] = progress

            if progress.completed_at is not None:
                continue

            current_cycle = max(1, progress.completion_count + 1)

            for step in target_steps:
                step_progress = None
                if step is not None:
                    step_progress = step_progress_map.get(step.id)
                    if step_progress is None:
                        step_progress = await self._repo.create_step_progress(
                            UserMissionStepProgress(
                                user_id=user.id,
                                mission_step_id=step.id,
                                required_count=max(1, step.required_count),
                                status=MissionProgressStatus.not_started,
                                progress_count=0,
                            )
                        )
                        step_progress_map[step.id] = step_progress
                    if step_progress.completed_at is not None:
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

                step_completed_now = False
                if step_progress is not None:
                    if step_progress.started_at is None:
                        step_progress.started_at = now
                    step_progress.last_event_at = now
                    step_progress.progress_count = min(
                        step_progress.required_count,
                        step_progress.progress_count + 1,
                    )
                    step_progress.status = MissionProgressStatus.in_progress
                    if step_progress.progress_count >= step_progress.required_count and step_progress.completed_at is None:
                        step_progress.status = MissionProgressStatus.completed
                        step_progress.completed_at = now
                        step_completed_now = True
                        if step.reward_credits > 0 and self._wallet_repo is not None:
                            await self._wallet_repo.adjust_balance(
                                user_id=user.id,
                                amount=step.reward_credits,
                                reason=CurrencyTransactionType.mission_reward,
                                context=f"mission_step:{mission.slug}:cycle:{current_cycle}:{step.id}",
                                source_id=step.id,
                                metadata={
                                    "mission_id": str(mission.id),
                                    "step_id": str(step.id),
                                    "reward_cycle": current_cycle,
                                },
                                now=now,
                            )
                    await self._repo.save_step_progress(step_progress)
                    step_progress_map[step.id] = step_progress
                else:
                    progress.progress_count = min(progress.required_count, progress.progress_count + 1)

                if mission.steps:
                    total_required = sum(max(1, s.required_count) for s in mission.steps)
                    total_progress = sum(
                        min(
                            step_progress_map.get(s.id).progress_count if step_progress_map.get(s.id) else 0,
                            max(1, s.required_count),
                        )
                        for s in mission.steps
                    )
                    progress.required_count = total_required
                    progress.progress_count = min(total_required, total_progress)

                completed_now = False
                if progress.progress_count >= progress.required_count and progress.completed_at is None:
                    progress.status = MissionProgressStatus.completed
                    progress.completed_at = now
                    progress.completion_count = current_cycle
                    reward_granted_at = await self._repo.grant_rewards(
                        user_id=user.id,
                        mission=mission,
                        reward_cycle=current_cycle,
                        now=now,
                        wallet_repo=self._wallet_repo,
                    )
                    progress.reward_granted_at = reward_granted_at
                    completed_slugs.append(mission.slug)
                    completed_now = True

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

    async def confirm_manual_step(self, user: User, slug: str) -> MissionRead:
        mission = await self._repo.get_mission_by_slug(slug)
        if mission is None:
            raise NotFoundError("mission", slug)
        if mission.action_type != MissionActionType.manual_confirmation:
            raise AppError(
                code="mission_manual_confirmation_not_allowed",
                message="Mission does not support manual confirmation",
                status_code=400,
            )
        await self.record_event(
            user=user,
            event_type="mission_manual_confirmed",
            source_event_key=f"mission_manual_confirmed:{user.id}:{mission.id}",
        )
        return await self.get_mission_by_slug(user, slug)
