import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.identity.model.admin import AdminTierUpdate
from app.modules.identity.model.user import UserRead
from app.modules.identity.repository.user_repository import UserRepository

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/users/{user_id}/tier", response_model=UserRead)
async def set_user_tier(
    user_id: uuid.UUID,
    body: AdminTierUpdate,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    repo = UserRepository(session)
    user = await repo.set_plan_tier(user_id, body.plan_tier)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)
