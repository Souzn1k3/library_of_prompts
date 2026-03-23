import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.infrastructure.db.models import PlanTier, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        try:
            await self._session.flush()
            await self._session.refresh(user)
        except IntegrityError as e:
            raise ConflictError("Email already registered") from e
        return user

    async def save(self, user: User) -> User:
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def set_plan_tier(self, user_id: uuid.UUID, tier: PlanTier) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.plan_tier = tier
        return await self.save(user)
