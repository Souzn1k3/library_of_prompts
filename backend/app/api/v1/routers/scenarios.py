from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_optional_user
from app.api.service_deps import get_scenario_service
from app.infrastructure.db.models import User
from app.modules.scenarios.model.scenario import (
    ScenarioHomeAggregateRead,
    ScenarioRunEventRead,
    ScenarioWorkspaceRead,
    ScenarioWorkspaceTrackWrite,
)
from app.modules.scenarios.service.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/aggregate", response_model=ScenarioHomeAggregateRead)
async def scenarios_home_aggregate(
    limit: int = Query(default=8, ge=3, le=24),
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioService = Depends(get_scenario_service),
) -> ScenarioHomeAggregateRead:
    return await svc.get_home_aggregate(viewer, limit=limit)


@router.get("/workspace", response_model=ScenarioWorkspaceRead)
async def scenarios_workspace(
    recent_limit: int = Query(default=8, ge=1, le=24),
    saved_limit: int = Query(default=24, ge=1, le=64),
    unfinished_limit: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    svc: ScenarioService = Depends(get_scenario_service),
) -> ScenarioWorkspaceRead:
    return await svc.get_workspace(
        current_user,
        recent_limit=recent_limit,
        saved_limit=saved_limit,
        unfinished_limit=unfinished_limit,
    )


@router.post("/workspace/track", response_model=ScenarioRunEventRead)
async def scenarios_workspace_track(
    body: ScenarioWorkspaceTrackWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioService = Depends(get_scenario_service),
) -> ScenarioRunEventRead:
    return await svc.track_workspace_action(current_user, body)
