from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import PromptStatus, User, UserScenarioWorkspace
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.catalog.model.recommendation import RecommendationContext
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.prompt_projection import to_list_item
from app.modules.catalog.service.recommendation_service import RecommendationService
from app.modules.marketplace.service.marketplace_service import MarketplaceService
from app.modules.scenarios.model.scenario import (
    ScenarioHomeAggregateRead,
    ScenarioLoopHintsRead,
    ScenarioRunEventRead,
    ScenarioWorkspaceAction,
    ScenarioWorkspaceItemRead,
    ScenarioWorkspaceLimitsRead,
    ScenarioWorkspaceRead,
    ScenarioWorkspaceTrackWrite,
)
from app.modules.scenarios.repository.scenario_workspace_repository import ScenarioWorkspaceRepository

DEFAULT_RECENT_LIMIT = 8
DEFAULT_SAVED_LIMIT = 24
DEFAULT_UNFINISHED_LIMIT = 6
DEFAULT_HOME_LIMIT = 8
DEFAULT_DEMO_RUNS = 3


class ScenarioService:
    def __init__(
        self,
        *,
        workspace_repo: ScenarioWorkspaceRepository,
        prompt_repo: PromptRepository,
        recommendation_service: RecommendationService,
        marketplace: MarketplaceService | None = None,
    ) -> None:
        self._workspace_repo = workspace_repo
        self._prompt_repo = prompt_repo
        self._recommendation_service = recommendation_service
        self._marketplace = marketplace

    async def get_workspace(
        self,
        viewer: User,
        *,
        recent_limit: int = DEFAULT_RECENT_LIMIT,
        saved_limit: int = DEFAULT_SAVED_LIMIT,
        unfinished_limit: int = DEFAULT_UNFINISHED_LIMIT,
    ) -> ScenarioWorkspaceRead:
        entries = await self._workspace_repo.list_workspace_entries(user_id=viewer.id)
        return await self._build_workspace(
            entries,
            viewer=viewer,
            recent_limit=recent_limit,
            saved_limit=saved_limit,
            unfinished_limit=unfinished_limit,
        )

    async def track_workspace_action(
        self,
        viewer: User,
        body: ScenarioWorkspaceTrackWrite,
    ) -> ScenarioRunEventRead:
        prompt = await self._prompt_repo.get_by_slug(body.prompt_slug)
        if prompt is None or prompt.status != PromptStatus.published:
            raise NotFoundError("prompt", body.prompt_slug)
        if prompt.category and prompt.category.is_restricted and not can_view_restricted_category(viewer):
            raise NotFoundError("prompt", body.prompt_slug)

        now = datetime.now(timezone.utc)
        entry = await self._workspace_repo.get_workspace_entry(user_id=viewer.id, prompt_id=prompt.id)
        if entry is None:
            entry = UserScenarioWorkspace(
                user_id=viewer.id,
                prompt_id=prompt.id,
                is_saved=False,
                run_count=0,
                copy_count=0,
                share_count=0,
                last_used_at=now,
                created_at=now,
                updated_at=now,
            )
            await self._workspace_repo.create_workspace_entry(entry)

        self._apply_action(entry, action=body.action, now=now, task_input=body.task_input)
        await self._workspace_repo.save_workspace_entry(entry)

        workspace = await self.get_workspace(viewer)
        return ScenarioRunEventRead(
            prompt_id=prompt.id,
            prompt_slug=prompt.slug,
            action=body.action,
            tracked_at=now,
            workspace=workspace,
        )

    async def get_home_aggregate(
        self,
        viewer: User | None,
        *,
        limit: int = DEFAULT_HOME_LIMIT,
    ) -> ScenarioHomeAggregateRead:
        recommendation = await self._recommendation_service.recommend(
            viewer,
            context=RecommendationContext.home,
            limit=limit,
        )
        sections = await self._recommendation_service.discovery_sections(viewer, limit=limit)

        featured = recommendation.items[:limit] if recommendation.items else sections.trending[:limit]
        recommended = sections.for_you[:limit] if sections.for_you else sections.trending[:limit]
        retention = sections.most_saved[:limit] if sections.most_saved else sections.best_for_beginners[:limit]

        workspace = await self.get_workspace(viewer) if viewer is not None else None

        return ScenarioHomeAggregateRead(
            generated_at=datetime.now(timezone.utc),
            featured=featured,
            recommended=recommended,
            retention=retention,
            workspace=workspace,
            workspace_limits=ScenarioWorkspaceLimitsRead(
                recent_limit=DEFAULT_RECENT_LIMIT,
                saved_limit=DEFAULT_SAVED_LIMIT,
                unfinished_limit=DEFAULT_UNFINISHED_LIMIT,
            ),
            loop_hints=ScenarioLoopHintsRead(
                core_loop_steps=[
                    "discover_scenario",
                    "run_scenario",
                    "save_or_share",
                    "resume_and_repeat",
                    "upgrade_for_full_blueprint",
                ],
                pro_capabilities=[
                    "full_scenario_blueprint",
                    "advanced_customization",
                    "saved_scenario_workspace",
                    "scenario_chain_execution",
                ],
                free_demo_runs_per_scenario=DEFAULT_DEMO_RUNS,
            ),
        )

    def _apply_action(
        self,
        entry: UserScenarioWorkspace,
        *,
        action: ScenarioWorkspaceAction,
        now: datetime,
        task_input: str | None,
    ) -> None:
        entry.last_used_at = now

        clean_task = (task_input or "").strip()

        if action == ScenarioWorkspaceAction.open:
            entry.last_opened_at = now
            if clean_task:
                entry.unfinished_task = clean_task
            return

        if action == ScenarioWorkspaceAction.run:
            entry.last_run_at = now
            entry.run_count = int(entry.run_count) + 1
            if clean_task:
                entry.unfinished_task = clean_task
            return

        if action == ScenarioWorkspaceAction.copy:
            entry.last_copied_at = now
            entry.copy_count = int(entry.copy_count) + 1
            return

        if action == ScenarioWorkspaceAction.share:
            entry.last_shared_at = now
            entry.share_count = int(entry.share_count) + 1
            return

        if action == ScenarioWorkspaceAction.save:
            entry.is_saved = True
            return

        if action == ScenarioWorkspaceAction.unsave:
            entry.is_saved = False
            return

        if action == ScenarioWorkspaceAction.unfinished_update:
            if not clean_task:
                return
            entry.unfinished_task = clean_task
            return

        if action == ScenarioWorkspaceAction.unfinished_clear:
            entry.unfinished_task = None

    async def _build_workspace(
        self,
        entries: list[UserScenarioWorkspace],
        *,
        viewer: User,
        recent_limit: int,
        saved_limit: int,
        unfinished_limit: int,
    ) -> ScenarioWorkspaceRead:
        prompt_ids = [entry.prompt_id for entry in entries]
        prompts = await self._prompt_repo.list_published_by_ids(
            prompt_ids,
            restrict_to_unrestricted_categories=not can_view_restricted_category(viewer),
        )
        prompt_by_id = {prompt.id: prompt for prompt in prompts}

        access_map = (
            await self._marketplace.build_access_map(list(prompts), viewer)
            if self._marketplace is not None
            else {}
        )

        items: list[ScenarioWorkspaceItemRead] = []
        for entry in entries:
            prompt = prompt_by_id.get(entry.prompt_id)
            if prompt is None:
                continue
            prompt_item = to_list_item(prompt, access=access_map.get(prompt.id))
            items.append(
                ScenarioWorkspaceItemRead(
                    prompt=PromptListItem.model_validate(prompt_item),
                    is_saved=bool(entry.is_saved),
                    unfinished_task=entry.unfinished_task,
                    run_count=int(entry.run_count),
                    copy_count=int(entry.copy_count),
                    share_count=int(entry.share_count),
                    last_used_at=entry.last_used_at,
                    last_run_at=entry.last_run_at,
                    last_opened_at=entry.last_opened_at,
                )
            )

        recent = sorted(items, key=lambda item: item.last_used_at, reverse=True)[:recent_limit]
        saved = [item for item in recent if item.is_saved]
        if len(saved) < saved_limit:
            remaining_saved = [item for item in items if item.is_saved and item.prompt.id not in {x.prompt.id for x in saved}]
            saved.extend(sorted(remaining_saved, key=lambda item: item.last_used_at, reverse=True))
        saved = saved[:saved_limit]

        unfinished = [item for item in items if item.unfinished_task]
        unfinished = sorted(unfinished, key=lambda item: item.last_used_at, reverse=True)[:unfinished_limit]

        return ScenarioWorkspaceRead(recent=recent, saved=saved, unfinished=unfinished)
