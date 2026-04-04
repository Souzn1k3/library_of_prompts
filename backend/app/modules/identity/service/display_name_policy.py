import uuid
from typing import Protocol

from app.core.errors import AppError, ConflictError
from app.infrastructure.db.models import User


class DisplayNameLookupProtocol(Protocol):
    async def get_by_display_name(self, display_name: str) -> User | None: ...


class DisplayNamePolicy:
    def normalize_required(self, value: str) -> str:
        display_name = value.strip()
        if not display_name:
            raise AppError(
                code="invalid_display_name",
                message="Display name is required",
                status_code=400,
                message_key="errors.invalid_display_name",
            )
        return display_name

    async def ensure_available(
        self,
        repo: DisplayNameLookupProtocol,
        display_name: str,
        *,
        exclude_user_id: uuid.UUID | None = None,
    ) -> None:
        existing = await repo.get_by_display_name(display_name)
        if existing is None:
            return
        if exclude_user_id is not None and existing.id == exclude_user_id:
            return
        raise ConflictError(
            "Display name already registered",
            message_key="errors.display_name_already_registered",
        )
