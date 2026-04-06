from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.catalog.model.prompt import PromptListItem


class ScenarioWorkspaceAction(str, enum.Enum):
    open = "open"
    run = "run"
    copy = "copy"
    share = "share"
    save = "save"
    unsave = "unsave"
    unfinished_update = "unfinished_update"
    unfinished_clear = "unfinished_clear"


class ScenarioWorkspaceTrackWrite(BaseModel):
    prompt_slug: str = Field(min_length=1, max_length=200)
    action: ScenarioWorkspaceAction
    task_input: str | None = Field(default=None, max_length=3000)


class ScenarioWorkspaceItemRead(BaseModel):
    prompt: PromptListItem
    is_saved: bool = False
    unfinished_task: str | None = None
    run_count: int = 0
    copy_count: int = 0
    share_count: int = 0
    last_used_at: datetime
    last_run_at: datetime | None = None
    last_opened_at: datetime | None = None


class ScenarioWorkspaceRead(BaseModel):
    recent: list[ScenarioWorkspaceItemRead]
    saved: list[ScenarioWorkspaceItemRead]
    unfinished: list[ScenarioWorkspaceItemRead]


class ScenarioWorkspaceLimitsRead(BaseModel):
    recent_limit: int
    saved_limit: int
    unfinished_limit: int


class ScenarioLoopHintsRead(BaseModel):
    core_loop_steps: list[str]
    pro_capabilities: list[str]
    free_demo_runs_per_scenario: int


class ScenarioHomeAggregateRead(BaseModel):
    generated_at: datetime
    featured: list[PromptListItem]
    recommended: list[PromptListItem]
    retention: list[PromptListItem]
    workspace: ScenarioWorkspaceRead | None = None
    workspace_limits: ScenarioWorkspaceLimitsRead
    loop_hints: ScenarioLoopHintsRead


class ScenarioRunEventRead(BaseModel):
    prompt_id: uuid.UUID
    prompt_slug: str
    action: ScenarioWorkspaceAction
    tracked_at: datetime
    workspace: ScenarioWorkspaceRead
