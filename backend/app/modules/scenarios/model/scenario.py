from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Literal

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
    packs: list["ScenarioPackRead"] = []
    chains: list["ScenarioChainRead"] = []
    next_steps: list["ScenarioNextStepRead"] = []
    return_triggers: list["ScenarioReturnTriggerRead"] = []
    showcase: list["ScenarioShowcaseRead"] = []
    pricing_plans: list["ScenarioPricingPlanRead"] = []
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
    bonus_runs_remaining: int | None = None


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


class ScenarioPackRead(BaseModel):
    id: str
    title: str
    description: str
    outcome: str
    prompt_slugs: list[str]
    prompts: list[PromptListItem]
    cta_prompt_slug: str | None = None


class ScenarioChainStepRead(BaseModel):
    position: int
    prompt_slug: str
    title: str
    goal: str


class ScenarioChainRead(BaseModel):
    id: str
    title: str
    description: str
    steps: list[ScenarioChainStepRead]


class ScenarioNextStepRead(BaseModel):
    source_prompt_slug: str | None = None
    next_prompt_slug: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class ScenarioReturnTriggerRead(BaseModel):
    trigger_key: str
    label: str
    count: int
    href: str


class ScenarioPricingPlanRead(BaseModel):
    tier: Literal["free", "starter", "pro", "enterprise"]
    price_monthly_usd: int
    headline: str
    highlights: list[str]


class ScenarioShowcaseCreateWrite(BaseModel):
    share_id: str | None = Field(default=None, min_length=8, max_length=120)
    prompt_slug: str | None = Field(default=None, min_length=1, max_length=200)
    blueprint_id: uuid.UUID | None = None
    title: str = Field(min_length=3, max_length=240)
    excerpt: str = Field(min_length=3, max_length=700)
    output_preview: str = Field(min_length=5, max_length=4000)
    visibility: Literal["public", "unlisted"] = "public"


class ScenarioShowcaseRead(BaseModel):
    share_id: str
    prompt_slug: str | None = None
    blueprint_id: uuid.UUID | None = None
    title: str
    excerpt: str
    output_preview: str
    visibility: str
    upvotes: int
    created_at: datetime


class ScenarioShowcaseUpvoteWrite(BaseModel):
    share_id: str = Field(min_length=8, max_length=120)


class ScenarioTokenBoostPurchaseWrite(BaseModel):
    prompt_slug: str = Field(min_length=1, max_length=200)


class ScenarioTokenBoostPurchaseRead(BaseModel):
    prompt_slug: str
    applied_bonus_runs: int
    bonus_runs_remaining: int
    token_cost: int
    balance_after: int | None = None
    is_pro: bool


class ScenarioBlueprintWrite(BaseModel):
    slug: str = Field(min_length=3, max_length=180)
    title: str = Field(min_length=3, max_length=260)
    summary: str | None = Field(default=None, max_length=700)
    category: Literal["utility", "learning", "productivity", "entertainment", "growth"] = "utility"
    input_schema: dict[str, Any] | None = None
    context_text: str | None = Field(default=None, max_length=4000)
    logic_text: str | None = Field(default=None, max_length=6000)
    output_text: str | None = Field(default=None, max_length=4000)
    run_instructions: str | None = Field(default=None, max_length=3000)
    source_prompt_slug: str | None = Field(default=None, max_length=200)
    visibility: Literal["private", "team", "public", "marketplace"] = "private"
    is_premium: bool = False
    token_price: int | None = Field(default=None, ge=1, le=10000)


class ScenarioBlueprintPatchWrite(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=260)
    summary: str | None = Field(default=None, max_length=700)
    category: Literal["utility", "learning", "productivity", "entertainment", "growth"] | None = None
    input_schema: dict[str, Any] | None = None
    context_text: str | None = Field(default=None, max_length=4000)
    logic_text: str | None = Field(default=None, max_length=6000)
    output_text: str | None = Field(default=None, max_length=4000)
    run_instructions: str | None = Field(default=None, max_length=3000)
    visibility: Literal["private", "team", "public", "marketplace"] | None = None
    is_premium: bool | None = None
    token_price: int | None = Field(default=None, ge=1, le=10000)


class ScenarioBlueprintRead(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    category: str
    visibility: str
    is_published: bool
    is_premium: bool
    token_price: int | None
    input_schema: dict[str, Any] | None
    context_text: str | None
    logic_text: str | None
    output_text: str | None
    run_instructions: str | None
    usage_count: int
    fork_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ScenarioBlueprintPublishRead(BaseModel):
    blueprint: ScenarioBlueprintRead
    creator_reward_tokens: int
    creator_reward_applied: bool


class ScenarioBlueprintShareWrite(BaseModel):
    member_email: str = Field(min_length=5, max_length=320)
    can_edit: bool = False


class ScenarioBlueprintShareRead(BaseModel):
    blueprint_id: uuid.UUID
    owner_user_id: uuid.UUID
    member_user_id: uuid.UUID
    can_edit: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioMarketplaceForkRead(BaseModel):
    source_blueprint_id: uuid.UUID
    forked_blueprint: ScenarioBlueprintRead
    token_spent: int = 0
    balance_after: int | None = None
    creator_reward_applied: bool = False


class ScenarioWorkflowWrite(BaseModel):
    name: str = Field(min_length=3, max_length=220)
    description: str | None = Field(default=None, max_length=600)
    visibility: Literal["private", "team", "public"] = "private"
    step_blueprint_ids: list[uuid.UUID] = Field(default_factory=list, min_length=1, max_length=16)


class ScenarioWorkflowRead(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    description: str | None
    visibility: str
    step_blueprint_ids: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScenarioWorkflowRunStartWrite(BaseModel):
    context: dict[str, Any] | None = None


class ScenarioWorkflowRunRead(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    current_step: int
    completed_steps: int
    total_steps: int
    next_blueprint_id: uuid.UUID | None = None
    completed_at: datetime | None = None
    last_active_at: datetime


class ScenarioWorkflowRunAdvanceWrite(BaseModel):
    mark_complete: bool = True


class ScenarioWorkflowRunAdvanceRead(BaseModel):
    run: ScenarioWorkflowRunRead
    is_completed: bool
    next_blueprint_id: uuid.UUID | None = None
