import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.modules.catalog.model.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.service.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(CategoryRepository(session))


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    parent_id: uuid.UUID | None = None,
    roots_only: bool = Query(default=False),
    svc: CategoryService = Depends(category_service),
) -> list[CategoryRead]:
    return await svc.list(parent_id=parent_id, roots_only=roots_only)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    svc: CategoryService = Depends(category_service),
) -> CategoryRead:
    return await svc.get_by_id(category_id)


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    body: CategoryCreate,
    svc: CategoryService = Depends(category_service),
) -> CategoryRead:
    return await svc.create(body)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    svc: CategoryService = Depends(category_service),
) -> CategoryRead:
    return await svc.update(category_id, body)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    svc: CategoryService = Depends(category_service),
) -> None:
    await svc.delete(category_id)
