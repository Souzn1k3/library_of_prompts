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


class ScenarioDemoRunTrackWrite(BaseModel):
    prompt_slug: str = Field(min_length=1, max_length=200)
    task_input: str | None = Field(default=None, max_length=3000)


class ScenarioDemoRunStatusRead(BaseModel):
    prompt_slug: str
    is_authenticated: bool
    is_pro: bool
    free_cap: int | None = None
    used_runs: int
    remaining_runs: int | None = None
    cap_reached: bool
    allowed: bool
    reason: str | None = None
    upgrade_hint: str | None = None
    guest_session_id: str | None = None


class ScenarioDemoRunTrackRead(BaseModel):
    executed: bool = False
    status: ScenarioDemoRunStatusRead
    workspace: ScenarioWorkspaceRead | None = None


class ScenarioGameEarnWrite(BaseModel):
    event_id: str = Field(min_length=8, max_length=120)
    challenge_id: str = Field(min_length=1, max_length=80)
    choice_index: int = Field(ge=0, le=10)


class ScenarioGameEarnRead(BaseModel):
    accepted: bool
    reason: str
    reward_tokens: int = 0
    pending_tokens: int = 0
    daily_cap_remaining: int = 0
    cooldown_seconds: int | None = None
    source: str = "web_demo"


class ScenarioGameStateRead(BaseModel):
    source: str = "web_demo"
    pending_tokens: int = 0
    claimable_tokens: int = 0
    claimed_tokens_today: int = 0
    daily_cap: int
    daily_cap_remaining: int
    cooldown_minutes: int
    needs_auth_to_claim: bool = True


class ScenarioGameClaimWrite(BaseModel):
    claim_id: str | None = Field(default=None, min_length=8, max_length=120)


class ScenarioGameClaimRead(BaseModel):
    claim_id: str
    source: str = "web_demo"
    applied: bool
    claimed_tokens: int = 0
    pending_tokens_after: int = 0
    balance_after: int | None = None
