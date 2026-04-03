import re
import uuid

from pydantic import BaseModel, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CategoryBase(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = 0
    is_restricted: bool = False

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        s = v.strip().lower()
        if not _SLUG_RE.match(s):
            raise ValueError("slug must be lowercase kebab-case")
        return s


class CategoryCreate(CategoryBase):
    parent_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    parent_id: uuid.UUID | None = None
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None
    is_restricted: bool | None = None

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip().lower()
        if not _SLUG_RE.match(s):
            raise ValueError("slug must be lowercase kebab-case")
        return s


class CategoryRead(CategoryBase):
    id: uuid.UUID
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}
