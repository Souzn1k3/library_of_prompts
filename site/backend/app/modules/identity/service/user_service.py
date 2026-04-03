import uuid
from typing import Protocol

from app.core.errors import NotFoundError
from app.infrastructure.db.models import User
from app.modules.identity.model.user import UserRead
from app.modules.identity.model.user_update import UserUpdateMe
from app.modules.identity.repository.user_repository import UserRepository


class UserRepositoryProtocol(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def save(self, user: User) -> User: ...


def _to_read(row: User) -> UserRead:
    return UserRead.model_validate(row)


class UserService:
    def __init__(self, repo: UserRepositoryProtocol) -> None:
        self._repo = repo

    async def get_by_id(self, user_id: uuid.UUID) -> UserRead:
        row = await self._repo.get_by_id(user_id)
        if row is None:
            raise NotFoundError("user", str(user_id))
        return _to_read(row)

    async def update_me(self, user_id: uuid.UUID, data: UserUpdateMe) -> UserRead:
        row = await self._repo.get_by_id(user_id)
        if row is None:
            raise NotFoundError("user", str(user_id))
        payload = data.model_dump(exclude_unset=True)
        if "display_name" in payload and payload["display_name"] is not None:
            row.display_name = payload["display_name"].strip()
        saved = await self._repo.save(row)
        return _to_read(saved)
