from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import PromptPurchase, PromptReview, User


class MarketplaceBaseMixin:
    async def rollback(self) -> None:
        await self._session.rollback()

    def _supports_for_update(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name != "sqlite")

    def _maybe_for_update(self, stmt: Select, enabled: bool) -> Select:
        if enabled and self._supports_for_update():
            return stmt.with_for_update()
        return stmt

    def _purchase_stmt(self) -> Select:
        return select(PromptPurchase).options(
            selectinload(PromptPurchase.prompt),
            selectinload(PromptPurchase.review),
            selectinload(PromptPurchase.review)
            .selectinload(PromptReview.author)
            .selectinload(User.contributor_profile),
        )
