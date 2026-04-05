import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, update

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LessonMission,
    MissionRewardType,
    User,
    UserMissionRewardGrant,
)


class MissionRepositoryRewardMixin:
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
        credit_override: int | None = None,
        credit_metadata: dict[str, Any] | None = None,
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

        reward_credits = mission.reward_credits if credit_override is None else max(0, int(credit_override))
        if reward_credits > 0:
            credit_granted = await self._grant_reward(
                user_id=user_id,
                mission_id=mission.id,
                reward_type=MissionRewardType.credits,
                reward_cycle=reward_cycle,
                badge_code=None,
                credits=reward_credits,
                premium_access_until=None,
                created_at=now,
            )
            if credit_granted:
                granted_any = True
                if wallet_repo is not None:
                    await wallet_repo.adjust_balance(
                        user_id=user_id,
                        amount=reward_credits,
                        reason=CurrencyTransactionType.mission_reward,
                        context=f"mission:{mission.slug}:cycle:{reward_cycle}",
                        source_id=mission.id,
                        metadata={
                            "mission_slug": mission.slug,
                            "reward_cycle": reward_cycle,
                            **(credit_metadata or {}),
                        },
                        now=now,
                    )
                else:
                    await self._session.execute(
                        update(User)
                        .where(User.id == user_id)
                        .values(mission_credits=User.mission_credits + reward_credits)
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
