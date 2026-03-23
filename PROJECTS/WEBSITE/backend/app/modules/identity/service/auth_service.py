import uuid

from app.core.errors import AppError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.infrastructure.db.models import User, UserRole
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.repository.user_repository import UserRepository


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def register(self, data: RegisterRequest) -> TokenResponse:
        email = data.email.lower()
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("Email already registered")

        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hash_password(data.password),
            display_name=data.display_name.strip(),
            role=UserRole.user,
        )
        created = await self._repo.create(user)

        token = create_access_token(subject_user_id=created.id)
        return TokenResponse(access_token=token)

    async def login(self, data: LoginRequest) -> TokenResponse:
        email = data.email.lower()
        user = await self._repo.get_by_email(email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise AppError(
                code="invalid_credentials",
                message="Invalid email or password",
                status_code=401,
            )
        token = create_access_token(subject_user_id=user.id)
        return TokenResponse(access_token=token)
