from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import get_current_user, get_optional_user
from app.api.service_deps import (
    get_scenario_demo_run_service,
    get_scenario_game_service,
    get_scenario_service,
)
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.infrastructure.db.models import User
from app.modules.scenarios.model.scenario import (
    ScenarioDemoRunStatusRead,
    ScenarioDemoRunTrackRead,
    ScenarioDemoRunTrackWrite,
    ScenarioGameClaimRead,
    ScenarioGameClaimWrite,
    ScenarioGameEarnRead,
    ScenarioGameEarnWrite,
    ScenarioGameStateRead,
    ScenarioHomeAggregateRead,
    ScenarioRunEventRead,
    ScenarioWorkspaceRead,
    ScenarioWorkspaceTrackWrite,
)
from app.modules.scenarios.service.scenario_demo_run_service import ScenarioDemoRunService
from app.modules.scenarios.service.scenario_game_service import ScenarioGameService
from app.modules.scenarios.service.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

_DEMO_RUN_TRACK_LIMITS: tuple[RateLimitRule, ...] = (
    RateLimitRule(key_template="scenarios:demo-run:track:ip:{ip}", limit=45, window_seconds=60),
    RateLimitRule(key_template="scenarios:demo-run:track:ip:{ip}", limit=300, window_seconds=3600),
)

_GAME_EARN_LIMITS: tuple[RateLimitRule, ...] = (
    RateLimitRule(key_template="scenarios:game:earn:ip:{ip}", limit=60, window_seconds=60),
    RateLimitRule(key_template="scenarios:game:earn:ip:{ip}", limit=400, window_seconds=3600),
)


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


@router.get("/demo-run/status", response_model=ScenarioDemoRunStatusRead)
async def scenarios_demo_run_status(
    request: Request,
    response: Response,
    prompt_slug: str = Query(min_length=1, max_length=200),
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioDemoRunService = Depends(get_scenario_demo_run_service),
) -> ScenarioDemoRunStatusRead:
    return await svc.get_status(
        prompt_slug=prompt_slug,
        viewer=viewer,
        request=request,
        response=response,
    )


@router.post("/demo-run/track", response_model=ScenarioDemoRunTrackRead)
async def scenarios_demo_run_track(
    request: Request,
    response: Response,
    body: ScenarioDemoRunTrackWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioDemoRunService = Depends(get_scenario_demo_run_service),
) -> ScenarioDemoRunTrackRead:
    await enforce_request_rate_limits(request, _DEMO_RUN_TRACK_LIMITS)
    return await svc.track_run(
        body=body,
        viewer=viewer,
        request=request,
        response=response,
    )


@router.get("/game/state", response_model=ScenarioGameStateRead)
async def scenarios_game_state(
    request: Request,
    response: Response,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioGameService = Depends(get_scenario_game_service),
) -> ScenarioGameStateRead:
    return await svc.get_state(
        viewer=viewer,
        request=request,
        response=response,
    )


@router.post("/game/earn", response_model=ScenarioGameEarnRead)
async def scenarios_game_earn(
    request: Request,
    response: Response,
    body: ScenarioGameEarnWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioGameService = Depends(get_scenario_game_service),
) -> ScenarioGameEarnRead:
    await enforce_request_rate_limits(request, _GAME_EARN_LIMITS)
    return await svc.earn(
        body=body,
        viewer=viewer,
        request=request,
        response=response,
    )


@router.post("/game/claim", response_model=ScenarioGameClaimRead)
async def scenarios_game_claim(
    request: Request,
    response: Response,
    body: ScenarioGameClaimWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioGameService = Depends(get_scenario_game_service),
) -> ScenarioGameClaimRead:
    return await svc.claim(
        body=body,
        viewer=viewer,
        request=request,
        response=response,
    )
