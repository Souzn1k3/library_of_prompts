import uuid

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import get_current_user, get_optional_user
from app.api.service_deps import (
    get_scenario_autonomy_service,
    get_scenario_demo_run_service,
    get_scenario_game_service,
    get_scenario_platform_service,
    get_scenario_service,
)
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.infrastructure.db.models import User
from app.modules.scenarios.model.scenario import (
    ScenarioAutonomyCycleRead,
    ScenarioAutonomyPersonalizationRead,
    ScenarioAutonomyRunWrite,
    ScenarioAutonomySelfCheckRead,
    ScenarioAutonomyStatusRead,
    ScenarioDemoRunStatusRead,
    ScenarioDemoRunTrackRead,
    ScenarioDemoRunTrackWrite,
    ScenarioGameClaimRead,
    ScenarioGameClaimWrite,
    ScenarioGameEarnRead,
    ScenarioGameEarnWrite,
    ScenarioGameStateRead,
    ScenarioMarketplaceForkRead,
    ScenarioNextStepRead,
    ScenarioPackRead,
    ScenarioBlueprintCommentRead,
    ScenarioBlueprintCommentWrite,
    ScenarioBlueprintLineageRead,
    ScenarioBlueprintPatchWrite,
    ScenarioBlueprintPublishRead,
    ScenarioBlueprintRatingRead,
    ScenarioBlueprintRatingWrite,
    ScenarioBlueprintRead,
    ScenarioBlueprintSaveRead,
    ScenarioBlueprintShareRead,
    ScenarioBlueprintShareWrite,
    ScenarioBlueprintUsageTrackRead,
    ScenarioBlueprintUsageTrackWrite,
    ScenarioBlueprintVersionRead,
    ScenarioBlueprintWrite,
    ScenarioChainRead,
    ScenarioShowcaseCreateWrite,
    ScenarioShowcaseRead,
    ScenarioShowcaseUpvoteWrite,
    ScenarioTokenBoostPurchaseRead,
    ScenarioTokenBoostPurchaseWrite,
    ScenarioWorkflowRead,
    ScenarioWorkflowRunAdvanceRead,
    ScenarioWorkflowRunStartWrite,
    ScenarioWorkflowRunRead,
    ScenarioWorkflowWrite,
    ScenarioHomeAggregateRead,
    ScenarioRunEventRead,
    ScenarioWorkspaceRead,
    ScenarioWorkspaceTrackWrite,
)
from app.modules.scenarios.service.scenario_demo_run_service import ScenarioDemoRunService
from app.modules.scenarios.service.scenario_game_service import ScenarioGameService
from app.modules.scenarios.service.scenario_autonomy_service import ScenarioAutonomyService
from app.modules.scenarios.service.scenario_platform_service import ScenarioPlatformService
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


@router.get("/packs", response_model=list[ScenarioPackRead])
async def scenarios_packs(
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioService = Depends(get_scenario_service),
) -> list[ScenarioPackRead]:
    aggregate = await svc.get_home_aggregate(viewer, limit=10)
    return aggregate.packs


@router.get("/chains", response_model=list[ScenarioChainRead])
async def scenarios_chains(
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioService = Depends(get_scenario_service),
) -> list[ScenarioChainRead]:
    aggregate = await svc.get_home_aggregate(viewer, limit=10)
    return aggregate.chains


@router.get("/next-step", response_model=ScenarioNextStepRead | None)
async def scenarios_next_step(
    prompt_slug: str | None = Query(default=None, min_length=1, max_length=200),
    viewer: User | None = Depends(get_optional_user),
    scenario_svc: ScenarioService = Depends(get_scenario_service),
    platform_svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioNextStepRead | None:
    aggregate = await scenario_svc.get_home_aggregate(viewer, limit=10)
    return await platform_svc.recommend_next(
        source_prompt_slug=prompt_slug,
        recommended=aggregate.recommended,
        chains=aggregate.chains,
    )


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


@router.post("/demo-run/boost-purchase", response_model=ScenarioTokenBoostPurchaseRead)
async def scenarios_demo_run_boost_purchase(
    body: ScenarioTokenBoostPurchaseWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioTokenBoostPurchaseRead:
    return await svc.purchase_demo_run_boost(viewer=current_user, prompt_slug=body.prompt_slug)


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


@router.get("/showcase", response_model=list[ScenarioShowcaseRead])
async def scenarios_showcase(
    limit: int = Query(default=24, ge=1, le=60),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioShowcaseRead]:
    return await svc.list_showcase(limit=limit)


@router.post("/showcase/share", response_model=ScenarioShowcaseRead)
async def scenarios_showcase_share(
    body: ScenarioShowcaseCreateWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioShowcaseRead:
    return await svc.create_showcase(viewer=viewer, body=body)


@router.post("/showcase/upvote", response_model=ScenarioShowcaseRead)
async def scenarios_showcase_upvote(
    body: ScenarioShowcaseUpvoteWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioShowcaseRead:
    return await svc.upvote_showcase(viewer=current_user, share_id=body.share_id)


@router.get("/studio/mine", response_model=list[ScenarioBlueprintRead])
async def scenarios_studio_mine(
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioBlueprintRead]:
    return await svc.list_my_blueprints(viewer=current_user)


@router.post("/studio", response_model=ScenarioBlueprintRead)
async def scenarios_studio_create(
    body: ScenarioBlueprintWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintRead:
    return await svc.create_blueprint(viewer=current_user, body=body)


@router.patch("/studio/{blueprint_id}", response_model=ScenarioBlueprintRead)
async def scenarios_studio_patch(
    blueprint_id: uuid.UUID,
    body: ScenarioBlueprintPatchWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintRead:
    return await svc.patch_blueprint(viewer=current_user, blueprint_id=blueprint_id, body=body)


@router.post("/studio/{blueprint_id}/publish", response_model=ScenarioBlueprintPublishRead)
async def scenarios_studio_publish(
    blueprint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintPublishRead:
    return await svc.publish_blueprint(viewer=current_user, blueprint_id=blueprint_id)


@router.get("/studio/{blueprint_id}/versions", response_model=list[ScenarioBlueprintVersionRead])
async def scenarios_studio_versions(
    blueprint_id: uuid.UUID,
    limit: int = Query(default=40, ge=1, le=120),
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioBlueprintVersionRead]:
    return await svc.list_blueprint_versions(
        viewer=current_user,
        blueprint_id=blueprint_id,
        limit=limit,
    )


@router.get("/studio/{blueprint_id}/lineage", response_model=ScenarioBlueprintLineageRead)
async def scenarios_studio_lineage(
    blueprint_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintLineageRead:
    return await svc.get_blueprint_lineage(viewer=viewer, blueprint_id=blueprint_id)


@router.post("/studio/{blueprint_id}/share", response_model=ScenarioBlueprintShareRead)
async def scenarios_studio_share(
    blueprint_id: uuid.UUID,
    body: ScenarioBlueprintShareWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintShareRead:
    return await svc.share_blueprint_with_member(viewer=current_user, blueprint_id=blueprint_id, body=body)


@router.get("/marketplace", response_model=list[ScenarioBlueprintRead])
async def scenarios_marketplace(
    limit: int = Query(default=24, ge=1, le=60),
    section: str = Query(default="trending", min_length=2, max_length=32),
    search: str | None = Query(default=None, max_length=140),
    category: str | None = Query(default=None, max_length=40),
    tags: str | None = Query(default=None, max_length=240),
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioBlueprintRead]:
    parsed_tags = [item.strip() for item in (tags or "").split(",") if item.strip()]
    return await svc.list_marketplace_blueprints(
        limit=limit,
        section=section,
        search=search,
        category=category,
        tags=parsed_tags,
        viewer=viewer,
    )


@router.post("/marketplace/{blueprint_id}/fork", response_model=ScenarioMarketplaceForkRead)
async def scenarios_marketplace_fork(
    blueprint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioMarketplaceForkRead:
    return await svc.fork_marketplace_blueprint(viewer=current_user, blueprint_id=blueprint_id)


@router.post("/marketplace/{blueprint_id}/remix", response_model=ScenarioMarketplaceForkRead)
async def scenarios_marketplace_remix(
    blueprint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioMarketplaceForkRead:
    return await svc.remix_marketplace_blueprint(viewer=current_user, blueprint_id=blueprint_id)


@router.post("/marketplace/{blueprint_id}/like", response_model=ScenarioBlueprintRead)
async def scenarios_marketplace_like(
    blueprint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintRead:
    return await svc.like_marketplace_blueprint(viewer=current_user, blueprint_id=blueprint_id)


@router.post("/marketplace/{blueprint_id}/save", response_model=ScenarioBlueprintSaveRead)
async def scenarios_marketplace_save(
    blueprint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintSaveRead:
    return await svc.toggle_save_blueprint(viewer=current_user, blueprint_id=blueprint_id)


@router.post("/marketplace/{blueprint_id}/rating", response_model=ScenarioBlueprintRatingRead)
async def scenarios_marketplace_rate(
    blueprint_id: uuid.UUID,
    body: ScenarioBlueprintRatingWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintRatingRead:
    return await svc.rate_blueprint(viewer=current_user, blueprint_id=blueprint_id, body=body)


@router.get("/marketplace/{blueprint_id}/comments", response_model=list[ScenarioBlueprintCommentRead])
async def scenarios_marketplace_comments(
    blueprint_id: uuid.UUID,
    limit: int = Query(default=30, ge=1, le=120),
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioBlueprintCommentRead]:
    return await svc.list_blueprint_comments(viewer=viewer, blueprint_id=blueprint_id, limit=limit)


@router.post("/marketplace/{blueprint_id}/comments", response_model=ScenarioBlueprintCommentRead)
async def scenarios_marketplace_comment_create(
    blueprint_id: uuid.UUID,
    body: ScenarioBlueprintCommentWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintCommentRead:
    return await svc.create_blueprint_comment(
        viewer=current_user,
        blueprint_id=blueprint_id,
        body=body,
    )


@router.post("/marketplace/{blueprint_id}/usage", response_model=ScenarioBlueprintUsageTrackRead)
async def scenarios_marketplace_track_usage(
    blueprint_id: uuid.UUID,
    body: ScenarioBlueprintUsageTrackWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioBlueprintUsageTrackRead:
    return await svc.track_blueprint_usage(
        viewer=viewer,
        blueprint_id=blueprint_id,
        body=body,
    )


@router.get("/workflows/mine", response_model=list[ScenarioWorkflowRead])
async def scenarios_workflows_mine(
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioWorkflowRead]:
    return await svc.list_my_workflows(viewer=current_user)


@router.post("/workflows", response_model=ScenarioWorkflowRead)
async def scenarios_workflows_create(
    body: ScenarioWorkflowWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioWorkflowRead:
    return await svc.create_workflow(viewer=current_user, body=body)


@router.post("/workflows/{workflow_id}/run", response_model=ScenarioWorkflowRunRead)
async def scenarios_workflows_run(
    workflow_id: uuid.UUID,
    body: ScenarioWorkflowRunStartWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioWorkflowRunRead:
    return await svc.start_workflow_run(viewer=current_user, workflow_id=workflow_id, body=body)


@router.post("/workflows/runs/{run_id}/advance", response_model=ScenarioWorkflowRunAdvanceRead)
async def scenarios_workflow_run_advance(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> ScenarioWorkflowRunAdvanceRead:
    return await svc.advance_workflow_run(viewer=current_user, run_id=run_id)


@router.get("/team/shared", response_model=list[ScenarioBlueprintRead])
async def scenarios_team_shared(
    current_user: User = Depends(get_current_user),
    svc: ScenarioPlatformService = Depends(get_scenario_platform_service),
) -> list[ScenarioBlueprintRead]:
    return await svc.list_team_shared_blueprints(viewer=current_user)


@router.post("/autonomy/run", response_model=ScenarioAutonomyCycleRead)
async def scenarios_autonomy_run(
    body: ScenarioAutonomyRunWrite,
    current_user: User = Depends(get_current_user),
    svc: ScenarioAutonomyService = Depends(get_scenario_autonomy_service),
) -> ScenarioAutonomyCycleRead:
    return await svc.run_autonomous_cycle(
        actor=current_user,
        trigger="manual",
        max_new_scenarios=body.max_new_scenarios,
        force=body.force,
    )


@router.get("/autonomy/status", response_model=ScenarioAutonomyStatusRead)
async def scenarios_autonomy_status(
    svc: ScenarioAutonomyService = Depends(get_scenario_autonomy_service),
) -> ScenarioAutonomyStatusRead:
    return await svc.get_status()


@router.get("/autonomy/self-check", response_model=ScenarioAutonomySelfCheckRead)
async def scenarios_autonomy_self_check(
    svc: ScenarioAutonomyService = Depends(get_scenario_autonomy_service),
) -> ScenarioAutonomySelfCheckRead:
    return await svc.get_self_check()


@router.get("/autonomy/personalization", response_model=ScenarioAutonomyPersonalizationRead)
async def scenarios_autonomy_personalization(
    current_user: User = Depends(get_current_user),
    svc: ScenarioAutonomyService = Depends(get_scenario_autonomy_service),
) -> ScenarioAutonomyPersonalizationRead:
    return await svc.get_personalization(viewer=current_user)
