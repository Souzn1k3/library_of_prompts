import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.errors import AppError, NotFoundError
from app.core.tiers import can_view_lesson, can_view_premium_content, can_view_restricted_category
from app.infrastructure.db.models import (
    LessonMission,
    MissionActionType,
    MissionProgressStatus,
    OnboardingProfile,
    PromptStatus,
    User,
    UserMissionProgress,
)
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
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._onboarding = onboarding_repo
        self._prompts = prompt_repo
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
    ) -> MissionNextStep | None:
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

    def _mission_read(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
    ) -> MissionRead:
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else max(1, mission.required_count)
        reward = MissionRewardView(
            badge=mission.reward_badge,
            credits=mission.reward_credits,
            premium_days=mission.reward_premium_days,
            granted_at=progress.reward_granted_at if progress else None,
        )
        next_step = self._mission_next_step(mission, prompts=prompts, lesson=lesson, status=status)
        return MissionRead(
            id=mission.id,
            slug=mission.slug,
            title=mission.title,
            description=mission.description,
            objective=mission.objective,
            completion_condition=mission.completion_condition,
            action_type=mission.action_type,
            status=status,
            progress_count=min(progress_count, required_count),
            required_count=required_count,
            started_at=progress.started_at if progress else None,
            last_event_at=progress.last_event_at if progress else None,
            completed_at=progress.completed_at if progress else None,
            prompts=prompts,
            lesson=lesson,
            reward=reward,
            next_step=next_step,
        )

    async def _build_missions(self, user: User) -> tuple[list[MissionRead], MissionRewardSummary]:
        profile = await self._onboarding.get_profile(user.id)
        can_view_premium = can_view_premium_content(user)
        fallback_prompts = await self._fallback_prompts(user, profile)

        all_missions = await self._repo.list_active_missions()
        eligible = [mission for mission in all_missions if self._is_eligible(mission, profile)]
        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}

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
            mission_views.append(self._mission_read(mission, progress, prompts=prompts, lesson=lesson_ref))

        credits, badges, premium_unlock_until = await self._repo.get_reward_summary(user.id)
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
    ) -> bool:
        linked_prompt_ids = {link.prompt_id for link in mission.prompt_links}
        if mission.action_type == MissionActionType.copy_prompt:
            if event_type != "prompt_copied":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if mission.action_type == MissionActionType.save_prompt:
            if event_type != "prompt_saved":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if mission.action_type == MissionActionType.copy_or_save_prompt:
            if event_type not in {"prompt_copied", "prompt_saved"}:
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if mission.action_type == MissionActionType.lesson_completed:
            if event_type != "lesson_completed":
                return False
            if mission.lesson_id and lesson_id != mission.lesson_id:
                return False
            return lesson_id is not None
        if mission.action_type == MissionActionType.onboarding_first_win:
            return event_type == "onboarding_first_win_completed"
        if mission.action_type == MissionActionType.manual_confirmation:
            return event_type == "mission_manual_confirmed"
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
        completed_slugs: list[str] = []

        for mission in eligible:
            if not self._matches_event(mission, event_type=event_type, prompt_id=prompt_id, lesson_id=lesson_id):
                continue

            progress = progress_map.get(mission.id)
            if progress is None:
                progress = await self._repo.create_progress(
                    UserMissionProgress(
                        user_id=user.id,
                        mission_id=mission.id,
                        required_count=max(1, mission.required_count),
                        status=MissionProgressStatus.not_started,
                        progress_count=0,
                    )
                )
                progress_map[mission.id] = progress

            if progress.completed_at is not None:
                continue

            scoped_key = source_event_key or f"{event_type}:{uuid.uuid4()}"
            completion_event = await self._repo.add_completion_event(
                progress_id=progress.id,
                user_id=user.id,
                mission_id=mission.id,
                event_type=event_type,
                source_event_key=f"{mission.id}:{scoped_key}",
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
            progress.progress_count = min(progress.required_count, progress.progress_count + 1)
            progress.status = MissionProgressStatus.in_progress

            completed_now = False
            if progress.progress_count >= progress.required_count and progress.completed_at is None:
                progress.status = MissionProgressStatus.completed
                progress.completed_at = now
                reward_granted_at = await self._repo.grant_rewards(user_id=user.id, mission=mission, now=now)
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
                progress=progress,
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
        progress: UserMissionProgress,
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
            "trigger_event_type": event_type,
            "progress_count": progress.progress_count,
            "required_count": progress.required_count,
            "prompt_id": str(prompt_id) if prompt_id is not None else None,
            "lesson_id": str(lesson_id) if lesson_id is not None else None,
        }

        if started_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_started,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_started:{user.id}:{mission.id}",
            )

        if not completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_progressed,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_progressed:{user.id}:{mission.id}:{progress.progress_count}:{source_event_key}",
            )

        if completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_completed,
                user_id=user.id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_completed:{user.id}:{mission.id}",
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
