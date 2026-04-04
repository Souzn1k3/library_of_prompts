import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError
from app.infrastructure.db.models import PlanTier, User


def _integrity_error_text(exc: IntegrityError) -> str:
    return str(getattr(exc, "orig", exc)).lower()


def _is_display_name_conflict(exc: IntegrityError) -> bool:
    text = _integrity_error_text(exc)
    return (
        "uq_users_display_name_ci" in text
        or "users.display_name" in text
        or ("display_name" in text and "unique" in text)
    )


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.contributor_profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_display_name(self, display_name: str) -> User | None:
        normalized = display_name.strip().lower()
        result = await self._session.execute(
            select(User).where(func.lower(func.trim(User.display_name)) == normalized)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        try:
            await self._session.flush()
            await self._session.refresh(user)
        except IntegrityError as e:
            if _is_display_name_conflict(e):
                raise ConflictError(
                    "Display name already registered",
                    message_key="errors.display_name_already_registered",
                ) from e
            raise ConflictError(
                "Email already registered",
                message_key="errors.email_already_registered",
            ) from e
        return user

    async def save(self, user: User) -> User:
        try:
            await self._session.flush()
            await self._session.refresh(user)
        except IntegrityError as e:
            if _is_display_name_conflict(e):
                raise ConflictError(
                    "Display name already registered",
                    message_key="errors.display_name_already_registered",
                ) from e
            raise
        return user

    async def set_plan_tier(self, user_id: uuid.UUID, tier: PlanTier) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.plan_tier = tier
        return await self.save(user)
