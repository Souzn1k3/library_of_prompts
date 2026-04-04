import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.i18n import SupportedLanguage
from app.core.errors import AppError, ConflictError, NotFoundError
from app.infrastructure.db.models import Category
from app.modules.catalog.model.category import CategoryCreate, CategoryRead, CategoryUpdate


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


_CATEGORY_NAME_OVERRIDES: dict[str, dict[SupportedLanguage, str]] = {
    "development": {"en": "Development", "ru": "Разработка", "tt": "Әзерләү"},
    "it": {
        "en": "Information Technology and Software Development",
        "ru": "Информационные технологии и разработка ПО",
        "tt": "Информацион технологияләр һәм ПО эшләү",
    },
    "marketing": {
        "en": "Marketing, Advertising and PR",
        "ru": "Маркетинг, реклама и PR",
        "tt": "Маркетинг, реклама һәм PR",
    },
    "business": {
        "en": "Business, Management and Entrepreneurship",
        "ru": "Бизнес, менеджмент и предпринимательство",
        "tt": "Бизнес, менеджмент һәм эшмәкәрлек",
    },
    "education": {"en": "Education and Science", "ru": "Образование и наука", "tt": "Мәгариф һәм фән"},
    "arts": {"en": "Creativity, Arts and Media", "ru": "Творчество, искусство и медиа", "tt": "Иҗат, сәнгать һәм медиа"},
    "engineering": {
        "en": "Engineering, Construction and Manufacturing",
        "ru": "Инженерия, строительство и производство",
        "tt": "Инженерия, төзелеш һәм җитештерү",
    },
    "finance": {"en": "Finance, Banking and Insurance", "ru": "Финансы, банкинг и страхование", "tt": "Финанс, банкинг һәм иминият"},
    "law": {"en": "Government and Law", "ru": "Государственное управление и право", "tt": "Дәүләт идарәсе һәм хокук"},
    "agro": {"en": "Agriculture and Ecology", "ru": "Сельское хозяйство и экология", "tt": "Авыл хуҗалыгы һәм экология"},
    "logistics": {
        "en": "Logistics, Transport and Tourism",
        "ru": "Логистика, транспорт и туризм",
        "tt": "Логистика, транспорт һәм туризм",
    },
    "real-estate": {"en": "Real Estate", "ru": "Недвижимость", "tt": "Күчемсез милек"},
    "lifestyle": {
        "en": "Personal Productivity and Lifestyle",
        "ru": "Персональная эффективность и lifestyle",
        "tt": "Шәхси нәтиҗәлелек һәм lifestyle",
    },
    "niche": {"en": "Specialized and Niche Fields", "ru": "Специализированные и нишевые области", "tt": "Махсуслашкан һәм ниша өлкәләре"},
}


def _looks_cyrillic(value: str) -> bool:
    return any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in value)


def _slug_title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-") if part)


def _localized_name(row: Category, language: SupportedLanguage) -> str:
    by_slug = _CATEGORY_NAME_OVERRIDES.get(row.slug)
    if by_slug:
        return by_slug.get(language) or by_slug.get("en") or row.name

    if language == "en" and _looks_cyrillic(row.name):
        return _slug_title(row.slug)
    return row.name


def _to_read(row: Category, *, language: SupportedLanguage) -> CategoryRead:
    return CategoryRead(
        id=row.id,
        parent_id=row.parent_id,
        slug=row.slug,
        name=_localized_name(row, language),
        sort_order=row.sort_order,
        is_restricted=row.is_restricted,
    )


def _to_read_raw(row: Category) -> CategoryRead:
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
        language: SupportedLanguage = "ru",
    ) -> list[CategoryRead]:
        rows = await self._repo.list(parent_id=parent_id, roots_only=roots_only)
        return [_to_read(r, language=language) for r in rows]

    async def get_by_id(self, category_id: uuid.UUID, *, language: SupportedLanguage = "ru") -> CategoryRead:
        row = await self._repo.get_by_id(category_id)
        if row is None:
            raise NotFoundError("category", str(category_id))
        return _to_read(row, language=language)

    async def get_by_slug(self, slug: str, *, language: SupportedLanguage = "ru") -> CategoryRead:
        row = await self._repo.get_by_slug(slug)
        if row is None:
            raise NotFoundError("category", slug)
        return _to_read(row, language=language)

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
            raise ConflictError(
                "We couldn't create this category. Check the name and parent category.",
                message_key="errors.category_create_conflict",
            ) from e
        return _to_read_raw(created)

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
                    message_key="errors.category_self_parent",
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
            raise ConflictError(
                "We couldn't update this category. Check the name and parent category.",
                message_key="errors.category_update_conflict",
            ) from e
        return _to_read_raw(updated)

    async def delete(self, category_id: uuid.UUID) -> None:
        row = await self._repo.get_by_id_or_raise(category_id)
        if await self._repo.count_children(category_id) > 0:
            raise AppError(
                code="category_has_children",
                message="Remove or move child categories first",
                status_code=400,
                message_key="errors.category_has_children",
            )
        if await self._repo.count_prompts(category_id) > 0:
            raise AppError(
                code="category_has_prompts",
                message="Reassign prompts before deleting this category",
                status_code=400,
                message_key="errors.category_has_prompts",
            )
        await self._repo.delete(row)
