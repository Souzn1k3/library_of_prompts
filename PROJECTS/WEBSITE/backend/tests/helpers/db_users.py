from __future__ import annotations

from sqlalchemy import update

from app.infrastructure.db.models import User, UserRole
from app.infrastructure.db.session import async_session_maker


async def set_user_role(*, email: str, role: UserRole) -> None:
    async with async_session_maker() as session:
        await session.execute(update(User).where(User.email == email.lower()).values(role=role))
        await session.commit()
