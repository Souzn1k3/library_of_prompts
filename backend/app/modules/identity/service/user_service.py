import uuid
from typing import Protocol

from app.core.errors import NotFoundError
from app.infrastructure.db.models import User
from app.modules.identity.model.user import UserRead
from app.modules.identity.model.user_update import UserUpdateMe
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.marketplace.service.marketplace_service import MarketplaceService
from app.modules.identity.service.display_name_policy import DisplayNamePolicy


class UserRepositoryProtocol(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    async def get_by_display_name(self, display_name: str) -> User | None: ...

    async def save(self, user: User) -> User: ...


def _to_read(row: User) -> UserRead:
    return UserRead.model_validate(row)


class UserService:
    def __init__(
        self,
        repo: UserRepositoryProtocol,
        contributors: ContributorService | None = None,
        marketplace: MarketplaceService | None = None,
        display_names: DisplayNamePolicy | None = None,
    ) -> None:
        self._repo = repo
        self._contributors = contributors
        self._marketplace = marketplace
        self._display_names = display_names or DisplayNamePolicy()

    async def _to_enriched_read(self, row: User) -> UserRead:
        base = UserRead.model_validate(row)
        contributor_slug = row.contributor_profile.slug if row.contributor_profile is not None else None
        if self._marketplace is None:
            return UserRead(**base.model_dump(), contributor_slug=contributor_slug)
        reputation_tier = row.contributor_profile.reputation_tier.value if row.contributor_profile is not None else None
        summary = await self._marketplace.seller_summary(
            seller_user_id=row.id,
            reputation_tier=reputation_tier,
            review_limit=3,
        )
        return UserRead(
            **base.model_dump(),
            contributor_slug=contributor_slug,
            rating_average=summary.rating_average,
            rating_display=summary.rating_display,
            review_count=summary.review_count,
            sold_prompts_count=summary.sold_prompts_count,
            purchases_count=summary.purchases_count,
            seller_revenue_rub=summary.seller_revenue_rub,
            seller_lumens_earned=summary.seller_lumens_earned,
            trust_indicators=summary.trust_indicators,
        )

    async def get_by_id(self, user_id: uuid.UUID) -> UserRead:
        row = await self._repo.get_by_id(user_id)
        if row is None:
            raise NotFoundError("user", str(user_id))
        return await self._to_enriched_read(row)

    async def update_me(self, user_id: uuid.UUID, data: UserUpdateMe) -> UserRead:
        row = await self._repo.get_by_id(user_id)
        if row is None:
            raise NotFoundError("user", str(user_id))
        payload = data.model_dump(exclude_unset=True)
        if "display_name" in payload and payload["display_name"] is not None:
            display_name = self._display_names.normalize_required(payload["display_name"])
            await self._display_names.ensure_available(
                self._repo,
                display_name,
                exclude_user_id=row.id,
            )
            row.display_name = display_name
        saved = await self._repo.save(row)
        if self._contributors is not None:
            await self._contributors.ensure_profile(saved)
        return await self._to_enriched_read(saved)
