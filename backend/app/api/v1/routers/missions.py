from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.service_deps import get_mission_service
from app.infrastructure.db.models import User
from app.modules.missions.model.mission import MissionCurrentRead, MissionListRead, MissionRead
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=MissionListRead)
async def list_missions(
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(get_mission_service),
) -> MissionListRead:
    return await svc.list_user_missions(current_user)


@router.get("/current", response_model=MissionCurrentRead)
async def current_mission(
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(get_mission_service),
) -> MissionCurrentRead:
    return await svc.current_user_mission(current_user)


@router.get("/{slug}", response_model=MissionRead)
async def mission_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(get_mission_service),
) -> MissionRead:
    return await svc.get_mission_by_slug(current_user, slug)


@router.post("/{slug}/confirm", response_model=MissionRead)
async def confirm_mission(
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(get_mission_service),
) -> MissionRead:
    return await svc.confirm_manual_step(current_user, slug)
