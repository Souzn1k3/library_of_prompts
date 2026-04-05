from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.infrastructure.db.models import ModelCompatibility, Tag, UseCase


class PromptRepositoryTaxonomyMixin:
    async def list_use_cases(self) -> Sequence[UseCase]:
        result = await self._session.execute(select(UseCase).order_by(UseCase.sort_order, UseCase.name))
        return result.scalars().all()

    async def list_model_compatibility(self) -> Sequence[ModelCompatibility]:
        result = await self._session.execute(
            select(ModelCompatibility).order_by(ModelCompatibility.sort_order, ModelCompatibility.name)
        )
        return result.scalars().all()

    async def list_tags(self) -> Sequence[Tag]:
        result = await self._session.execute(select(Tag).order_by(Tag.name))
        return result.scalars().all()

    async def get_use_cases_by_slugs(self, slugs: Sequence[str]) -> Sequence[UseCase]:
        if not slugs:
            return []
        result = await self._session.execute(select(UseCase).where(UseCase.slug.in_(list(slugs))))
        return result.scalars().all()

    async def get_model_compatibility_by_slugs(self, slugs: Sequence[str]) -> Sequence[ModelCompatibility]:
        if not slugs:
            return []
        result = await self._session.execute(
            select(ModelCompatibility).where(ModelCompatibility.slug.in_(list(slugs)))
        )
        return result.scalars().all()

    async def get_tags_by_slugs(self, slugs: Sequence[str]) -> Sequence[Tag]:
        if not slugs:
            return []
        result = await self._session.execute(select(Tag).where(Tag.slug.in_(list(slugs))))
        return result.scalars().all()
