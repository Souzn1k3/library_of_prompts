import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LessonMission,
    LessonMissionPrompt,
    MissionStep,
    MissionCompletionEvent,
    MissionProgressStatus,
    MissionRewardType,
    SavedPrompt,
    User,
    UserMissionProgress,
    UserMissionStepProgress,
    UserMissionRewardGrant,
)


class MissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    async def list_active_missions(self) -> list[LessonMission]:
        stmt = (
            select(LessonMission)
            .where(LessonMission.is_active.is_(True))
            .options(
                selectinload(LessonMission.lesson),
                selectinload(LessonMission.prompt_links).selectinload(LessonMissionPrompt.prompt),
                selectinload(LessonMission.steps)
                .selectinload(MissionStep.target_prompt),
                selectinload(LessonMission.steps)
                .selectinload(MissionStep.target_lesson),
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
                selectinload(LessonMission.steps)
                .selectinload(MissionStep.target_prompt),
                selectinload(LessonMission.steps)
                .selectinload(MissionStep.target_lesson),
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

    async def create_progress(self, progress: UserMissionProgress) -> UserMissionProgress:
        self._session.add(progress)
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def create_step_progress(self, progress: UserMissionStepProgress) -> UserMissionStepProgress:
        self._session.add(progress)
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def save_progress(self, progress: UserMissionProgress) -> UserMissionProgress:
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def save_step_progress(self, progress: UserMissionStepProgress) -> UserMissionStepProgress:
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def reset_progress_cycle(
        self,
        *,
        progress: UserMissionProgress,
        step_progress_rows: list[UserMissionStepProgress],
    ) -> None:
        progress.status = MissionProgressStatus.not_started
        progress.progress_count = 0
        progress.started_at = None
        progress.last_event_at = None
        progress.completed_at = None
        progress.reward_granted_at = None

        for row in step_progress_rows:
            row.status = MissionProgressStatus.not_started
            row.progress_count = 0
            row.started_at = None
            row.last_event_at = None
            row.completed_at = None

        await self._session.flush()

    async def add_completion_event(
        self,
        *,
        progress_id: uuid.UUID,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        mission_step_id: uuid.UUID | None,
        event_type: str,
        source_event_key: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        payload: dict[str, Any] | None,
        created_at: datetime,
    ) -> MissionCompletionEvent | None:
        stmt = (
            self._insert(MissionCompletionEvent)
            .values(
                progress_id=progress_id,
                user_id=user_id,
                mission_id=mission_id,
                mission_step_id=mission_step_id,
                event_type=event_type,
                source_event_key=source_event_key,
                prompt_id=prompt_id,
                lesson_id=lesson_id,
                payload=payload,
                created_at=created_at,
            )
            .on_conflict_do_nothing(index_elements=["source_event_key"])
        )
        if not self._is_sqlite():
            stmt = stmt.returning(MissionCompletionEvent.id)
            result = await self._session.execute(stmt)
            event_id = result.scalar_one_or_none()
            if event_id is None:
                return None
            row = await self._session.execute(
                select(MissionCompletionEvent).where(MissionCompletionEvent.id == event_id)
            )
            return row.scalar_one_or_none()

        result = await self._session.execute(stmt)
        if int(result.rowcount or 0) <= 0:
            return None
        row = await self._session.execute(
            select(MissionCompletionEvent).where(MissionCompletionEvent.source_event_key == source_event_key)
        )
        return row.scalar_one_or_none()

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

    async def _grant_reward(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        reward_type: MissionRewardType,
        reward_cycle: int,
        badge_code: str | None,
        credits: int,
        premium_access_until: datetime | None,
        created_at: datetime,
    ) -> bool:
        stmt = (
            self._insert(UserMissionRewardGrant)
            .values(
                user_id=user_id,
                mission_id=mission_id,
                reward_type=reward_type,
                reward_cycle=reward_cycle,
                badge_code=badge_code,
                credits=credits,
                premium_access_until=premium_access_until,
                created_at=created_at,
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "mission_id", "reward_type", "reward_cycle"],
            )
        )
        if not self._is_sqlite():
            stmt = stmt.returning(UserMissionRewardGrant.id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None

        result = await self._session.execute(stmt)
        return int(result.rowcount or 0) > 0

    async def grant_rewards(
        self,
        *,
        user_id: uuid.UUID,
        mission: LessonMission,
        reward_cycle: int,
        now: datetime,
        wallet_repo=None,
    ) -> datetime | None:
        granted_any = False

        if mission.reward_badge:
            granted_any = (
                await self._grant_reward(
                    user_id=user_id,
                    mission_id=mission.id,
                    reward_type=MissionRewardType.badge,
                    reward_cycle=1,
                    badge_code=mission.reward_badge,
                    credits=0,
                    premium_access_until=None,
                    created_at=now,
                )
                or granted_any
            )

        if mission.reward_credits > 0:
            credit_granted = await self._grant_reward(
                user_id=user_id,
                mission_id=mission.id,
                reward_type=MissionRewardType.credits,
                reward_cycle=reward_cycle,
                badge_code=None,
                credits=mission.reward_credits,
                premium_access_until=None,
                created_at=now,
            )
            if credit_granted:
                granted_any = True
                if wallet_repo is not None:
                    await wallet_repo.adjust_balance(
                        user_id=user_id,
                        amount=mission.reward_credits,
                        reason=CurrencyTransactionType.mission_reward,
                        context=f"mission:{mission.slug}:cycle:{reward_cycle}",
                        source_id=mission.id,
                        metadata={"mission_slug": mission.slug, "reward_cycle": reward_cycle},
                        now=now,
                    )
                else:
                    await self._session.execute(
                        update(User)
                        .where(User.id == user_id)
                        .values(mission_credits=User.mission_credits + mission.reward_credits)
                    )

        if mission.reward_premium_days > 0:
            premium_until = now + timedelta(days=mission.reward_premium_days)
            premium_granted = await self._grant_reward(
                user_id=user_id,
                mission_id=mission.id,
                reward_type=MissionRewardType.premium_unlock,
                reward_cycle=reward_cycle,
                badge_code=None,
                credits=0,
                premium_access_until=premium_until,
                created_at=now,
            )
            if premium_granted:
                granted_any = True
                current_unlock = (
                    await self._session.execute(
                        select(User.premium_unlock_until).where(User.id == user_id)
                    )
                ).scalar_one_or_none()

                next_unlock = premium_until
                if current_unlock is not None:
                    current_unlock_dt = (
                        current_unlock
                        if current_unlock.tzinfo is not None
                        else current_unlock.replace(tzinfo=now.tzinfo)
                    )
                    if current_unlock_dt > premium_until:
                        next_unlock = current_unlock_dt

                await self._session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(premium_unlock_until=next_unlock)
                )

        return now if granted_any else None

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
