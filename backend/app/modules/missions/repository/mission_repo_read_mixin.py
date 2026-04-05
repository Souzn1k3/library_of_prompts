import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    LessonMission,
    LessonMissionPrompt,
    MissionCompletionEvent,
    MissionRewardType,
    MissionStep,
    SavedPrompt,
    User,
    UserMissionProgress,
    UserMissionRewardGrant,
    UserMissionStepProgress,
)


class MissionRepositoryReadMixin:
    async def list_active_missions(self) -> list[LessonMission]:
        stmt = (
            select(LessonMission)
            .where(LessonMission.is_active.is_(True))
            .options(
                selectinload(LessonMission.lesson),
                selectinload(LessonMission.prompt_links).selectinload(LessonMissionPrompt.prompt),
                selectinload(LessonMission.steps).selectinload(MissionStep.target_prompt),
                selectinload(LessonMission.steps).selectinload(MissionStep.target_lesson),
            )
            .order_by(LessonMission.sort_order.asc(), LessonMission.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_mission_by_slug(self, slug: str) -> LessonMission | None:
        stmt = (
            select(LessonMission)
            .where(LessonMission.slug == slug, LessonMission.is_active.is_(True))
            .options(
                selectinload(LessonMission.lesson),
                selectinload(LessonMission.prompt_links).selectinload(LessonMissionPrompt.prompt),
                selectinload(LessonMission.steps).selectinload(MissionStep.target_prompt),
                selectinload(LessonMission.steps).selectinload(MissionStep.target_lesson),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_progress(self, user_id: uuid.UUID) -> list[UserMissionProgress]:
        stmt = select(UserMissionProgress).where(UserMissionProgress.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_user_step_progress(self, user_id: uuid.UUID) -> list[UserMissionStepProgress]:
        stmt = select(UserMissionStepProgress).where(UserMissionStepProgress.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_progress(self, user_id: uuid.UUID, mission_id: uuid.UUID) -> UserMissionProgress | None:
        stmt = select(UserMissionProgress).where(
            UserMissionProgress.user_id == user_id,
            UserMissionProgress.mission_id == mission_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent_completion_events(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 24,
    ) -> list[MissionCompletionEvent]:
        result = await self._session.execute(
            select(MissionCompletionEvent)
            .where(MissionCompletionEvent.user_id == user_id)
            .order_by(MissionCompletionEvent.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_reward_summary(self, user_id: uuid.UUID) -> tuple[int, list[str], datetime | None]:
        user_row = await self._session.execute(
            select(User.mission_credits, User.premium_unlock_until).where(User.id == user_id)
        )
        credits_row = user_row.one_or_none()
        credits = int(credits_row[0]) if credits_row else 0
        premium_unlock_until = credits_row[1] if credits_row else None

        badge_rows = await self._session.execute(
            select(UserMissionRewardGrant.badge_code)
            .where(
                UserMissionRewardGrant.user_id == user_id,
                UserMissionRewardGrant.reward_type == MissionRewardType.badge,
                UserMissionRewardGrant.badge_code.is_not(None),
            )
            .order_by(UserMissionRewardGrant.created_at.asc())
        )
        badges: list[str] = []
        for row in badge_rows.fetchall():
            badge = row[0]
            if badge and badge not in badges:
                badges.append(badge)
        return credits, badges, premium_unlock_until

    async def user_has_saved_prompts(self, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(SavedPrompt).where(SavedPrompt.user_id == user_id)
        )
        return int(result.scalar_one() or 0) > 0
