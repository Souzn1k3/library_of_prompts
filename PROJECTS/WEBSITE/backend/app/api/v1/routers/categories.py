import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_optional_user, require_admin
from app.api.service_deps import get_category_service
from app.core.cache import get_cache
from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import User
from app.modules.catalog.model.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.catalog.service.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])
_CATEGORY_CACHE_TTL = 180


def _category_visibility(viewer: User | None) -> str:
    return "all" if can_view_restricted_category(viewer) else "public"


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    parent_id: uuid.UUID | None = None,
    roots_only: bool = Query(default=False),
    viewer: User | None = Depends(get_optional_user),
    svc: CategoryService = Depends(get_category_service),
) -> list[CategoryRead]:
    visibility = _category_visibility(viewer)
    cache = get_cache()
    parent = str(parent_id) if parent_id is not None else "none"
    suffix = f"list:parent={parent}:roots={int(roots_only)}:visibility={visibility}"

    async def loader() -> list[CategoryRead]:
        rows = await svc.list(parent_id=parent_id, roots_only=roots_only)
        if visibility == "all":
            return rows
        return [r for r in rows if not r.is_restricted]

    return await cache.get_or_set_json(
        namespace="categories",
        suffix=suffix,
        loader=loader,
        ttl_seconds=_CATEGORY_CACHE_TTL,
    )


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    visibility = _category_visibility(viewer)
    cache = get_cache()
    suffix = f"get:id={category_id}:visibility={visibility}"

    async def loader() -> CategoryRead:
        row = await svc.get_by_id(category_id)
        if row.is_restricted and visibility != "all":
            raise NotFoundError("category", str(category_id))
        return row

    return await cache.get_or_set_json(
        namespace="categories",
        suffix=suffix,
        loader=loader,
        ttl_seconds=_CATEGORY_CACHE_TTL,
    )


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    body: CategoryCreate,
    _admin: User = Depends(require_admin),
    svc: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    created = await svc.create(body)
    await get_cache().bump_many(("categories", "prompts"))
    return created


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    _admin: User = Depends(require_admin),
    svc: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    updated = await svc.update(category_id, body)
    await get_cache().bump_many(("categories", "prompts"))
    return updated


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    svc: CategoryService = Depends(get_category_service),
) -> None:
    await svc.delete(category_id)
    await get_cache().bump_many(("categories", "prompts"))
