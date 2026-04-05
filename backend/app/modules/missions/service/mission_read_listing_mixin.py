from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import NotFoundError
from app.core.tiers import can_view_lesson, can_view_premium_content, can_view_restricted_category
from app.infrastructure.db.models import (
    LessonMission,
    MissionProgressStatus,
    OnboardingProfile,
    PromptStatus,
    User,
    UserMissionProgress,
)
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.catalog.model.prompt import PromptSort
from app.modules.missions.model.mission import (
    MissionCurrentRead,
    MissionLessonRef,
    MissionListRead,
    MissionPromptRef,
    MissionRead,
    MissionRewardSummary,
)
from app.modules.missions.service.mission_constants import STREAK_RECOVERY_MISSION_SLUG
from app.modules.onboarding.service.persona_hints import build_persona_hint_query


class MissionReadListingMixin:
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

    def _mission_sort_key(
        self,
        mission: LessonMission,
        *,
        profile: OnboardingProfile | None,
        segment: str,
        progress: UserMissionProgress | None,
    ) -> tuple[int, int, int, str]:
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

    def _mission_lesson_ref(self, mission: LessonMission, user: User) -> MissionLessonRef | None:
        if mission.lesson is None:
            return None
        return MissionLessonRef(
            id=mission.lesson.id,
            slug=mission.lesson.slug,
            title=mission.lesson.title,
            min_tier=mission.lesson.min_tier,
            locked=not can_view_lesson(user, mission.lesson.min_tier),
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

        ordered = sorted(
            eligible,
            key=lambda mission: self._mission_sort_key(
                mission,
                profile=profile,
                segment=segment,
                progress=progress_map.get(mission.id),
            ),
        )
        mission_views: list[MissionRead] = []
        for mission in ordered:
            progress = progress_map.get(mission.id)
            prompts = self._mission_prompts(
                mission,
                can_view_premium=can_view_premium,
                fallback_prompts=fallback_prompts,
            )
            mission_views.append(
                self._mission_read(
                    mission,
                    progress,
                    user=user,
                    segment=segment,
                    prompts=prompts,
                    lesson=self._mission_lesson_ref(mission, user),
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
