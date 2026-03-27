from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.infrastructure.db.session import get_db
from app.modules.contributors.model.contributor import ContributorProfileRead, ContributorTopItem
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.identity.repository.user_repository import UserRepository

router = APIRouter(prefix="/contributors", tags=["contributors"])
_CONTRIBUTOR_CACHE_TTL = 90


def contributor_service(session: AsyncSession = Depends(get_db)) -> ContributorService:
    return ContributorService(ContributorRepository(session), UserRepository(session))


@router.get("/top", response_model=list[ContributorTopItem])
async def top_contributors(
    limit: int = Query(default=12, ge=1, le=50),
    svc: ContributorService = Depends(contributor_service),
) -> list[ContributorTopItem]:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="contributors",
        suffix=f"top:limit={limit}",
        loader=lambda: svc.list_top(limit=limit),
        ttl_seconds=_CONTRIBUTOR_CACHE_TTL,
    )


@router.get("/{slug}", response_model=ContributorProfileRead)
async def contributor_profile(
    slug: str,
    svc: ContributorService = Depends(contributor_service),
) -> ContributorProfileRead:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="contributors",
        suffix=f"profile:slug={slug.strip().lower()}",
        loader=lambda: svc.get_public_profile(slug),
        ttl_seconds=_CONTRIBUTOR_CACHE_TTL,
    )
