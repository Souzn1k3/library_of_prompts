from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import ContributorProfile, Prompt, User


class MarketplacePromptMixin:
    async def get_contributor_slug_for_user(self, user_id: uuid.UUID) -> str | None:
        stmt = select(ContributorProfile.slug).where(ContributorProfile.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_prompt_by_id(self, prompt_id: uuid.UUID) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                selectinload(Prompt.pricing),
                selectinload(Prompt.author).selectinload(User.contributor_profile),
            )
            .where(Prompt.id == prompt_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_prompt_by_slug(self, slug: str) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                selectinload(Prompt.pricing),
                selectinload(Prompt.author).selectinload(User.contributor_profile),
            )
            .where(Prompt.slug == slug)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
