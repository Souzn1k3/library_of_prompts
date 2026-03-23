import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.infrastructure.db.models import Category
from app.modules.catalog.model.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.modules.catalog.repository.category_repository import CategoryRepository


class CategoryRepositoryProtocol(Protocol):
    async def list(
        self, *, parent_id: uuid.UUID | None = None, roots_only: bool = False
    ) -> Sequence[Category]: ...

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None: ...

    async def get_by_slug(self, slug: str) -> Category | None: ...

    async def count_children(self, category_id: uuid.UUID) -> int: ...

    async def count_prompts(self, category_id: uuid.UUID) -> int: ...

    async def create(self, category: Category) -> Category: ...

    async def update(self, category: Category) -> Category: ...

    async def delete(self, category: Category) -> None: ...

    async def get_by_id_or_raise(self, category_id: uuid.UUID) -> Category: ...


def _to_read(row: Category) -> CategoryRead:
    return CategoryRead(
        id=row.id,
        parent_id=row.parent_id,
        slug=row.slug,
        name=row.name,
        sort_order=row.sort_order,
        is_restricted=row.is_restricted,
    )


class CategoryService:
    def __init__(self, repo: CategoryRepositoryProtocol) -> None:
        self._repo = repo

    async def list(
        self,
        *,
        parent_id: uuid.UUID | None = None,
        roots_only: bool = False,
    ) -> list[CategoryRead]:
        rows = await self._repo.list(parent_id=parent_id, roots_only=roots_only)
        return [_to_read(r) for r in rows]

    async def get_by_id(self, category_id: uuid.UUID) -> CategoryRead:
        row = await self._repo.get_by_id(category_id)
        if row is None:
            raise NotFoundError("category", str(category_id))
        return _to_read(row)

    async def get_by_slug(self, slug: str) -> CategoryRead:
        row = await self._repo.get_by_slug(slug)
        if row is None:
            raise NotFoundError("category", slug)
        return _to_read(row)

    async def create(self, data: CategoryCreate) -> CategoryRead:
        if data.parent_id is not None:
            await self._repo.get_by_id_or_raise(data.parent_id)

        row = Category(
            parent_id=data.parent_id,
            slug=data.slug,
            name=data.name,
            sort_order=data.sort_order,
            is_restricted=data.is_restricted,
        )
        try:
            created = await self._repo.create(row)
        except IntegrityError as e:
            raise ConflictError("Could not create category (slug or parent conflict)") from e
        return _to_read(created)

    async def update(self, category_id: uuid.UUID, data: CategoryUpdate) -> CategoryRead:
        row = await self._repo.get_by_id_or_raise(category_id)
        payload = data.model_dump(exclude_unset=True)

        if "parent_id" in payload:
            pid = payload["parent_id"]
            if pid == category_id:
                raise AppError(
                    code="invalid_parent",
                    message="Category cannot be its own parent",
                    status_code=400,
                )
            if pid is not None:
                await self._repo.get_by_id_or_raise(pid)
            row.parent_id = pid

        if "slug" in payload and payload["slug"] is not None:
            row.slug = payload["slug"]
        if "name" in payload and payload["name"] is not None:
            row.name = payload["name"]
        if "sort_order" in payload:
            row.sort_order = payload["sort_order"]
        if "is_restricted" in payload:
            row.is_restricted = payload["is_restricted"]

        try:
            updated = await self._repo.update(row)
        except IntegrityError as e:
            raise ConflictError("Could not update category (slug or parent conflict)") from e
        return _to_read(updated)

    async def delete(self, category_id: uuid.UUID) -> None:
        row = await self._repo.get_by_id_or_raise(category_id)
        if await self._repo.count_children(category_id) > 0:
            raise AppError(
                code="category_has_children",
                message="Remove or move child categories first",
                status_code=400,
            )
        if await self._repo.count_prompts(category_id) > 0:
            raise AppError(
                code="category_has_prompts",
                message="Reassign prompts before deleting this category",
                status_code=400,
            )
        await self._repo.delete(row)
