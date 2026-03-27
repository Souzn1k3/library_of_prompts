import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.errors import AppError
from app.core.security import parse_user_id_from_token
from app.infrastructure.db.models import User, UserRole
from app.infrastructure.db.session import get_db
from app.modules.identity.repository.user_repository import UserRepository

security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)


def _extract_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    settings = get_settings()
    if credentials is not None and settings.legacy_bearer_auth_enabled:
        if credentials.scheme.lower() == "bearer":
            return credentials.credentials
    cookie_token = request.cookies.get(settings.access_token_cookie_name)
    if cookie_token:
        return cookie_token
    return None


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> uuid.UUID:
    token = _extract_access_token(request, credentials)
    if not token:
        raise AppError(
            code="not_authenticated",
            message="Please log in to continue.",
            status_code=401,
            message_key="errors.invalid_or_expired_token",
        )
    try:
        return parse_user_id_from_token(token)
    except ValueError as e:
        raise AppError(
            code="invalid_token",
            message="Your session has expired. Please log in again.",
            status_code=401,
            message_key="errors.invalid_or_expired_token",
        ) from e


async def get_current_user(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> User:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise AppError(
            code="user_not_found",
            message="We couldn't find your account.",
            status_code=401,
            message_key="errors.user_not_found",
        )
    return user


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> User | None:
    token = _extract_access_token(request, credentials)
    if token is None:
        return None
    try:
        uid = parse_user_id_from_token(token)
    except ValueError:
        return None
    repo = UserRepository(session)
    return await repo.get_by_id(uid)


def require_roles(*roles: UserRole):
    async def _inner(current: User = Depends(get_current_user)) -> User:
        if current.role not in roles:
            raise AppError(
                code="insufficient_permissions",
                message="You don't have access to this action.",
                status_code=403,
                message_key="errors.insufficient_permissions",
            )
        return current

    return _inner


require_moderator = require_roles(UserRole.moderator, UserRole.admin)
require_admin = require_roles(UserRole.admin)
