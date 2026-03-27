import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import OnboardingEvent, OnboardingProfile


class OnboardingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile(self, user_id: uuid.UUID) -> OnboardingProfile | None:
        result = await self._session.execute(
            select(OnboardingProfile).where(OnboardingProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(self, profile: OnboardingProfile) -> OnboardingProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def save_profile(self, profile: OnboardingProfile) -> OnboardingProfile:
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def add_event(
        self,
        *,
        user_id: uuid.UUID,
        event_name: str,
        payload: dict | None = None,
    ) -> OnboardingEvent:
        event = OnboardingEvent(
            user_id=user_id,
            event_name=event_name,
            payload=payload,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event
