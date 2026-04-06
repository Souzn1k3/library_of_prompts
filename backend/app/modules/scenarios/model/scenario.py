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
    tags: list[str] = Field(default_factory=list, max_length=20)
    metadata: dict[str, Any] | None = None
    input_schema: dict[str, Any] | None = None
    context_text: str | None = Field(default=None, max_length=4000)
    logic_text: str | None = Field(default=None, max_length=6000)
    output_text: str | None = Field(default=None, max_length=4000)
    run_instructions: str | None = Field(default=None, max_length=3000)
    source_prompt_slug: str | None = Field(default=None, max_length=200)
    visibility: Literal["private", "team", "public", "marketplace", "premium"] = "private"
    monetization_mode: Literal["free", "pro_only", "paid"] = "free"
    is_premium: bool = False
    token_price: int | None = Field(default=None, ge=1, le=10000)


class ScenarioBlueprintPatchWrite(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=260)
    summary: str | None = Field(default=None, max_length=700)
    category: Literal["utility", "learning", "productivity", "entertainment", "growth"] | None = None
    tags: list[str] | None = Field(default=None, max_length=20)
    metadata: dict[str, Any] | None = None
    input_schema: dict[str, Any] | None = None
    context_text: str | None = Field(default=None, max_length=4000)
    logic_text: str | None = Field(default=None, max_length=6000)
    output_text: str | None = Field(default=None, max_length=4000)
    run_instructions: str | None = Field(default=None, max_length=3000)
    visibility: Literal["private", "team", "public", "marketplace", "premium"] | None = None
    monetization_mode: Literal["free", "pro_only", "paid"] | None = None
    is_premium: bool | None = None
    token_price: int | None = Field(default=None, ge=1, le=10000)


class ScenarioBlueprintRead(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    category: str
    tags: list[str]
    metadata: dict[str, Any] | None = None
    author_display_name: str | None = None
    visibility: str
    monetization_mode: str
    autonomous_mode: bool = False
    autonomous_stage: str = "manual"
    autonomous_quality_score: float = 0.0
    autonomous_target_segment: str | None = None
    autonomous_last_iteration_at: datetime | None = None
    is_published: bool
    is_premium: bool
    token_price: int | None
    input_schema: dict[str, Any] | None
    context_text: str | None
    logic_text: str | None
    output_text: str | None
    run_instructions: str | None
    usage_count: int
    run_count: int
    completion_count: int
    save_count: int
    fork_count: int
    like_count: int
    comment_count: int
    rating_average: float
    rating_count: int
    version_number: int
    forked_from_id: uuid.UUID | None = None
    root_blueprint_id: uuid.UUID | None = None
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


class ScenarioBlueprintVersionRead(BaseModel):
    id: uuid.UUID
    blueprint_id: uuid.UUID
    version_number: int
    snapshot_json: dict[str, Any]
    change_note: str | None = None
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioBlueprintLineageNodeRead(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    owner_user_id: uuid.UUID
    version_number: int
    forked_from_id: uuid.UUID | None = None
    root_blueprint_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioBlueprintLineageRead(BaseModel):
    root_blueprint_id: uuid.UUID
    chain: list[ScenarioBlueprintLineageNodeRead]
    children: list[ScenarioBlueprintLineageNodeRead]


class ScenarioBlueprintCommentWrite(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ScenarioBlueprintCommentRead(BaseModel):
    id: uuid.UUID
    blueprint_id: uuid.UUID
    author_user_id: uuid.UUID | None = None
    author_display_name: str | None = None
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScenarioBlueprintRatingWrite(BaseModel):
    rating: int = Field(ge=1, le=5)


class ScenarioBlueprintRatingRead(BaseModel):
    blueprint_id: uuid.UUID
    rating: int
    rating_average: float
    rating_count: int


class ScenarioBlueprintSaveRead(BaseModel):
    blueprint_id: uuid.UUID
    saved: bool
    save_count: int


class ScenarioBlueprintUsageTrackWrite(BaseModel):
    event: Literal["run", "complete"]


class ScenarioBlueprintUsageTrackRead(BaseModel):
    blueprint_id: uuid.UUID
    event: Literal["run", "complete"]
    usage_count: int
    run_count: int
    completion_count: int


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


class ScenarioAutonomyRunWrite(BaseModel):
    force: bool = False
    max_new_scenarios: int | None = Field(default=None, ge=1, le=10)


class ScenarioAutonomyNeedSignalRead(BaseModel):
    source: Literal["search", "failed_runs", "popular_actions", "retention_gap"]
    key: str
    strength: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0)


class ScenarioAutonomyExperimentRead(BaseModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    blueprint_id: uuid.UUID | None = None
    experiment_key: str
    dimension: Literal["scenario", "ui", "pricing", "paywall"]
    status: str
    control_variant: str
    treatment_variant: str
    winner_variant: str | None = None
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    outcome_metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None


class ScenarioAutonomyGrowthDecisionRead(BaseModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    source: str
    campaign: str | None = None
    action: Literal["scale_channel", "kill_channel", "adjust_budget", "adjust_pricing", "adjust_paywall"]
    rationale: dict[str, Any] = Field(default_factory=dict)
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    guardrail_passed: bool = True
    created_at: datetime


class ScenarioAutonomyGuardrailRead(BaseModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    scope: Literal["scenario", "ui", "pricing", "growth", "marketplace"]
    rule_key: str
    severity: Literal["info", "warning", "critical"] = "warning"
    triggered: bool
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ScenarioAutonomySelfCheckRead(BaseModel):
    creates_new_scenarios: bool
    tests_autonomously: bool
    makes_decisions_autonomously: bool
    improves_without_human: bool
    all_passed: bool


class ScenarioAutonomyCycleRead(BaseModel):
    id: uuid.UUID
    trigger: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    generated_count: int = 0
    published_count: int = 0
    iterations_count: int = 0
    signals: list[ScenarioAutonomyNeedSignalRead] = Field(default_factory=list)
    experiments: list[ScenarioAutonomyExperimentRead] = Field(default_factory=list)
    growth_decisions: list[ScenarioAutonomyGrowthDecisionRead] = Field(default_factory=list)
    guardrails: list[ScenarioAutonomyGuardrailRead] = Field(default_factory=list)
    self_check: ScenarioAutonomySelfCheckRead


class ScenarioAutonomyStatusRead(BaseModel):
    enabled: bool
    scheduler_enabled: bool
    latest_cycle: ScenarioAutonomyCycleRead | None = None
    total_cycles: int = 0
    self_check: ScenarioAutonomySelfCheckRead


class ScenarioAutonomyPersonalizationRead(BaseModel):
    user_id: uuid.UUID
    ui_variant: str
    paywall_variant: str
    pricing_variant: str
    preferred_categories: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    recommended_blueprints: list[ScenarioBlueprintRead] = Field(default_factory=list)
    updated_at: datetime
