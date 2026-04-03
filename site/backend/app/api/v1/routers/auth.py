from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(session))


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    svc: AuthService = Depends(auth_service),
) -> TokenResponse:
    return await svc.register(body)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    svc: AuthService = Depends(auth_service),
) -> TokenResponse:
    return await svc.login(body)
