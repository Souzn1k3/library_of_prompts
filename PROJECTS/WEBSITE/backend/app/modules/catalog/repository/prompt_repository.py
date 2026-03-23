import uuid
from collections.abc import Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    Category,
    ModerationState,
    Prompt,
    PromptStatus,
    PromptTechnique,
)


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _published_filters(
        self,
        *,
        q: str | None,
        category_id: uuid.UUID | None,
        technique: PromptTechnique | None,
        restrict_to_unrestricted_categories: bool,
    ):
        parts = [Prompt.status == PromptStatus.published]
        if category_id is not None:
            parts.append(Prompt.category_id == category_id)
        if technique is not None:
            parts.append(Prompt.technique == technique)
        if q and q.strip():
            term = f"%{q.strip()}%"
            parts.append(
                or_(
                    Prompt.title.ilike(term),
                    Prompt.summary.ilike(term),
                    Prompt.body.ilike(term),
                )
            )
        if restrict_to_unrestricted_categories:
            parts.append(Category.is_restricted.is_(False))
        return and_(*parts)

    async def list_published(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        restrict_to_unrestricted_categories: bool = False,
    ) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .where(
                self._published_filters(
                    q=q,
                    category_id=category_id,
                    technique=technique,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
            )
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count_published(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        restrict_to_unrestricted_categories: bool = False,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .where(
                self._published_filters(
                    q=q,
                    category_id=category_id,
                    technique=technique,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_by_slug(self, slug: str) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(selectinload(Prompt.category))
            .where(Prompt.slug == slug)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(selectinload(Prompt.category))
            .where(Prompt.id == prompt_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, prompt: Prompt) -> Prompt:
        self._session.add(prompt)
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt

    async def save(self, prompt: Prompt) -> Prompt:
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt

    async def list_moderation_queue(self, *, skip: int = 0, limit: int = 50) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .options(selectinload(Prompt.category))
            .where(
                Prompt.status == PromptStatus.draft,
                Prompt.moderation_state == ModerationState.pending,
            )
            .order_by(Prompt.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_author(
        self, author_id: uuid.UUID, *, skip: int = 0, limit: int = 50
    ) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .where(Prompt.author_id == author_id)
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
