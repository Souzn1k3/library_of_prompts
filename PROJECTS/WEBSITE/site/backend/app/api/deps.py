import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import parse_user_id_from_token
from app.infrastructure.db.models import User, UserRole
from app.infrastructure.db.session import get_db
from app.modules.identity.repository.user_repository import UserRepository

security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    try:
        return parse_user_id_from_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


async def get_current_user(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> User:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> User | None:
    if credentials is None:
        return None
    try:
        uid = parse_user_id_from_token(credentials.credentials)
    except ValueError:
        return None
    repo = UserRepository(session)
    return await repo.get_by_id(uid)


def require_roles(*roles: UserRole):
    async def _inner(current: User = Depends(get_current_user)) -> User:
        if current.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current

    return _inner


require_moderator = require_roles(UserRole.moderator, UserRole.admin)
require_admin = require_roles(UserRole.admin)
