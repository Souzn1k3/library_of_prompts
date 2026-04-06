from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.config import Settings
from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    PlanTier,
    PromptStatus,
    ScenarioCreatorRewardEvent,
    ScenarioOutputShowcase,
    User,
    UserScenarioBlueprint,
    UserScenarioBlueprintShare,
    UserScenarioRunBoost,
    UserScenarioWorkflow,
    UserScenarioWorkflowRun,
)
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.prompt_projection import to_list_item
from app.modules.economy.service.wallet_service import WalletService
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.scenarios.model.scenario import (
    ScenarioBlueprintPatchWrite,
    ScenarioBlueprintPublishRead,
    ScenarioBlueprintRead,
    ScenarioBlueprintShareRead,
    ScenarioBlueprintShareWrite,
    ScenarioBlueprintWrite,
    ScenarioChainRead,
    ScenarioChainStepRead,
    ScenarioMarketplaceForkRead,
    ScenarioNextStepRead,
    ScenarioPackRead,
    ScenarioPricingPlanRead,
    ScenarioReturnTriggerRead,
    ScenarioShowcaseCreateWrite,
    ScenarioShowcaseRead,
    ScenarioTokenBoostPurchaseRead,
    ScenarioWorkflowRead,
    ScenarioWorkflowRunAdvanceRead,
    ScenarioWorkflowRunRead,
    ScenarioWorkflowRunStartWrite,
    ScenarioWorkflowWrite,
    ScenarioWorkspaceRead,
)
from app.modules.scenarios.repository.scenario_demo_repository import ScenarioDemoRepository
from app.modules.scenarios.repository.scenario_platform_repository import ScenarioPlatformRepository

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_PACK_TEMPLATES = (
    {
        "id": "activation-sprint",
        "title": "Activation Sprint",
        "description": "Get first value in under 10 seconds and secure a repeatable run.",
        "outcome": "First output + saved continuation point.",
        "keywords": ("launch", "onboarding", "first", "quick", "start"),
    },
    {
        "id": "operator-pack",
        "title": "Operator Pack",
        "description": "Move from investigation to execution with less context-switching.",
        "outcome": "Research -> generation -> validation cycle.",
        "keywords": ("analysis", "debug", "workflow", "plan", "qa"),
    },
    {
        "id": "revenue-pack",
        "title": "Revenue Pack",
        "description": "Focus on scenarios that create direct upgrade pressure and shareable outcomes.",
        "outcome": "Conversion-ready outputs for monetization tasks.",
        "keywords": ("growth", "sales", "retention", "conversion", "marketing"),
    },
)

_CHAIN_TEMPLATES = (
    {
        "id": "research-generate-ship",
        "title": "Research -> Generate -> Ship",
        "description": "Three-step scenario chain to go from problem framing to final asset.",
        "steps": (
            {"goal": "Clarify constraints and edge-cases.", "keywords": ("research", "analysis", "brief", "audit")},
            {"goal": "Generate a strong first draft.", "keywords": ("generate", "write", "draft", "plan")},
            {"goal": "Finalize and prepare for handoff.", "keywords": ("review", "validate", "final", "qa")},
        ),
    },
    {
        "id": "learn-apply-repeat",
        "title": "Learn -> Apply -> Repeat",
        "description": "Habit loop for retention: understand pattern, run it, then improve.",
        "steps": (
            {"goal": "Learn the pattern.", "keywords": ("learn", "explain", "lesson", "study")},
            {"goal": "Apply on your task.", "keywords": ("task", "workflow", "apply", "execute")},
            {"goal": "Capture and reuse.", "keywords": ("save", "template", "repeat", "improve")},
        ),
    },
)


def _normalize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not _SLUG_RE.match(normalized):
        raise AppError(
            code="invalid_slug",
            message="Use lowercase letters, numbers, and hyphens for scenario slug.",
            status_code=400,
        )
    return normalized


def _prompt_tokens(prompt: PromptListItem) -> str:
    parts = [
        prompt.title,
        prompt.summary or "",
        *list(prompt.use_cases or []),
        *list(prompt.tags or []),
    ]
    return " ".join(parts).lower().replace("_", " ").replace("-", " ")


def _blueprint_to_read(row: UserScenarioBlueprint) -> ScenarioBlueprintRead:
    return ScenarioBlueprintRead.model_validate(row)


def _workflow_to_read(row: UserScenarioWorkflow) -> ScenarioWorkflowRead:
    return ScenarioWorkflowRead.model_validate(row)


def _showcase_to_read(row: ScenarioOutputShowcase) -> ScenarioShowcaseRead:
    return ScenarioShowcaseRead(
        share_id=row.share_id,
        prompt_slug=row.prompt_slug,
        blueprint_id=row.blueprint_id,
        title=row.title,
        excerpt=row.excerpt,
        output_preview=row.output_preview,
        visibility=row.visibility,
        upvotes=int(row.upvotes),
        created_at=row.created_at,
    )


class ScenarioPlatformService:
    def __init__(
        self,
        *,
        repo: ScenarioPlatformRepository,
        demo_repo: ScenarioDemoRepository,
        prompt_repo: PromptRepository,
        user_repo: UserRepository,
        wallet: WalletService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._demo_repo = demo_repo
        self._prompt_repo = prompt_repo
        self._user_repo = user_repo
        self._wallet = wallet
        self._settings = settings

    async def build_home_growth_surfaces(
        self,
        *,
        featured: list[PromptListItem],
        recommended: list[PromptListItem],
        retention: list[PromptListItem],
        workspace: ScenarioWorkspaceRead | None,
    ) -> dict[str, list]:
        prompt_pool = self._dedupe_prompts([*featured, *recommended, *retention])[:24]
        packs = self._build_packs(prompt_pool)
        chains = self._build_chains(prompt_pool)
        next_steps = self._build_next_steps(workspace=workspace, recommended=recommended, chains=chains)
        return_triggers = self._build_return_triggers(workspace=workspace)
        showcase = await self.list_showcase(limit=8)
        pricing_plans = self._pricing_plans()
        return {
            "packs": packs,
            "chains": chains,
            "next_steps": next_steps,
            "return_triggers": return_triggers,
            "showcase": showcase,
            "pricing_plans": pricing_plans,
        }

    def _dedupe_prompts(self, prompts: list[PromptListItem]) -> list[PromptListItem]:
        by_id: dict[uuid.UUID, PromptListItem] = {}
        for prompt in prompts:
            by_id[prompt.id] = prompt
        return list(by_id.values())

    def _match_prompt_by_keywords(
        self,
        *,
        prompts: list[PromptListItem],
        keywords: tuple[str, ...],
        used_slugs: set[str],
    ) -> PromptListItem | None:
        for prompt in prompts:
            if prompt.slug in used_slugs:
                continue
            tokens = _prompt_tokens(prompt)
            if any(keyword in tokens for keyword in keywords):
                return prompt
        return None

    def _build_packs(self, prompts: list[PromptListItem]) -> list[ScenarioPackRead]:
        packs: list[ScenarioPackRead] = []
        cursor = 0
        for template in _PACK_TEMPLATES:
            used_slugs: set[str] = set()
            selected: list[PromptListItem] = []
            for keyword in template["keywords"]:
                matched = self._match_prompt_by_keywords(
                    prompts=prompts,
                    keywords=(keyword,),
                    used_slugs=used_slugs,
                )
                if matched is None:
                    continue
                selected.append(matched)
                used_slugs.add(matched.slug)
                if len(selected) >= 3:
                    break
            while len(selected) < 3 and cursor < len(prompts):
                fallback = prompts[cursor]
                cursor += 1
                if fallback.slug in used_slugs:
                    continue
                selected.append(fallback)
                used_slugs.add(fallback.slug)
            if not selected:
                continue
            packs.append(
                ScenarioPackRead(
                    id=template["id"],
                    title=template["title"],
                    description=template["description"],
                    outcome=template["outcome"],
                    prompt_slugs=[item.slug for item in selected],
                    prompts=selected,
                    cta_prompt_slug=selected[0].slug,
                )
            )
        return packs

    def _build_chains(self, prompts: list[PromptListItem]) -> list[ScenarioChainRead]:
        chains: list[ScenarioChainRead] = []
        fallback_index = 0
        for template in _CHAIN_TEMPLATES:
            used_slugs: set[str] = set()
            steps: list[ScenarioChainStepRead] = []
            for index, step in enumerate(template["steps"], start=1):
                prompt = self._match_prompt_by_keywords(
                    prompts=prompts,
                    keywords=tuple(step["keywords"]),
                    used_slugs=used_slugs,
                )
                while prompt is None and fallback_index < len(prompts):
                    candidate = prompts[fallback_index]
                    fallback_index += 1
                    if candidate.slug in used_slugs:
                        continue
                    prompt = candidate
                if prompt is None:
                    continue
                used_slugs.add(prompt.slug)
                steps.append(
                    ScenarioChainStepRead(
                        position=index,
                        prompt_slug=prompt.slug,
                        title=prompt.title,
                        goal=step["goal"],
                    )
                )
            if not steps:
                continue
            chains.append(
                ScenarioChainRead(
                    id=template["id"],
                    title=template["title"],
                    description=template["description"],
                    steps=steps,
                )
            )
        return chains

    def _build_next_steps(
        self,
        *,
        workspace: ScenarioWorkspaceRead | None,
        recommended: list[PromptListItem],
        chains: list[ScenarioChainRead],
    ) -> list[ScenarioNextStepRead]:
        next_steps: list[ScenarioNextStepRead] = []
        if workspace and workspace.unfinished:
            unfinished = workspace.unfinished[0]
            unfinished_slug = unfinished.prompt.slug
            for chain in chains:
                for index, step in enumerate(chain.steps):
                    if step.prompt_slug != unfinished_slug:
                        continue
                    if index + 1 >= len(chain.steps):
                        continue
                    next_step = chain.steps[index + 1]
                    next_steps.append(
                        ScenarioNextStepRead(
                            source_prompt_slug=unfinished_slug,
                            next_prompt_slug=next_step.prompt_slug,
                            reason=f"Continue chain: {chain.title}",
                            confidence=0.92,
                        )
                    )
                    break
                if next_steps:
                    break

        used = {item.next_prompt_slug for item in next_steps}
        recent_slug = workspace.recent[0].prompt.slug if workspace and workspace.recent else None
        for prompt in recommended:
            if prompt.slug == recent_slug or prompt.slug in used:
                continue
            next_steps.append(
                ScenarioNextStepRead(
                    source_prompt_slug=recent_slug,
                    next_prompt_slug=prompt.slug,
                    reason="Recommended from your latest usage pattern.",
                    confidence=0.78,
                )
            )
            if len(next_steps) >= 3:
                break
        return next_steps

    def _build_return_triggers(self, *, workspace: ScenarioWorkspaceRead | None) -> list[ScenarioReturnTriggerRead]:
        if workspace is None:
            return [
                ScenarioReturnTriggerRead(
                    trigger_key="signup_workspace",
                    label="Create workspace to save and resume scenarios.",
                    count=1,
                    href="/signup",
                )
            ]

        triggers: list[ScenarioReturnTriggerRead] = []
        if workspace.unfinished:
            triggers.append(
                ScenarioReturnTriggerRead(
                    trigger_key="unfinished_runs",
                    label="Unfinished scenarios waiting for completion",
                    count=len(workspace.unfinished),
                    href="/#home-workbench",
                )
            )
        if workspace.saved:
            triggers.append(
                ScenarioReturnTriggerRead(
                    trigger_key="saved_replays",
                    label="Saved scenarios ready for replay",
                    count=len(workspace.saved),
                    href="/dashboard",
                )
            )
        if workspace.recent:
            triggers.append(
                ScenarioReturnTriggerRead(
                    trigger_key="recent_context",
                    label="Recent runs can be resumed in one click",
                    count=len(workspace.recent),
                    href="/#home-workbench",
                )
            )
        return triggers

    def _pricing_plans(self) -> list[ScenarioPricingPlanRead]:
        return [
            ScenarioPricingPlanRead(
                tier="free",
                price_monthly_usd=0,
                headline="Try value-first scenarios instantly.",
                highlights=[
                    "Result-first previews",
                    "Limited demo runs per scenario",
                    "Game rewards and pending claims",
                ],
            ),
            ScenarioPricingPlanRead(
                tier="starter",
                price_monthly_usd=12,
                headline="Unlock full scenario blueprints and customization.",
                highlights=[
                    "Unlimited scenario runs",
                    "Save and resume workspace",
                    "Scenario chain execution",
                ],
            ),
            ScenarioPricingPlanRead(
                tier="pro",
                price_monthly_usd=29,
                headline="Scale with marketplace, workflows, and collaboration.",
                highlights=[
                    "Advanced workflow runs",
                    "Creator studio and publishing",
                    "Team sharing + marketplace forks",
                ],
            ),
            ScenarioPricingPlanRead(
                tier="enterprise",
                price_monthly_usd=99,
                headline="Team operations with platform-level scenario governance.",
                highlights=[
                    "Shared scenario operations",
                    "High-volume workflow usage",
                    "Priority support and rollout controls",
                ],
            ),
        ]

    async def purchase_demo_run_boost(
        self,
        *,
        viewer: User,
        prompt_slug: str,
    ) -> ScenarioTokenBoostPurchaseRead:
        prompt = await self._prompt_repo.get_by_slug(prompt_slug)
        if prompt is None or prompt.status != PromptStatus.published:
            raise NotFoundError("prompt", prompt_slug)

        if viewer.plan_tier != PlanTier.free:
            boost = await self._demo_repo.get_user_run_boost(user_id=viewer.id, prompt_id=prompt.id)
            return ScenarioTokenBoostPurchaseRead(
                prompt_slug=prompt.slug,
                applied_bonus_runs=0,
                bonus_runs_remaining=int(boost.bonus_runs_remaining) if boost else 0,
                token_cost=0,
                balance_after=None,
                is_pro=True,
            )

        cost = int(self._settings.scenario_run_boost_token_cost)
        bonus_runs = int(self._settings.scenario_run_boost_bonus_runs)
        now = datetime.now(timezone.utc)

        await self._wallet.ensure_wallet(viewer.id)
        transaction = await self._wallet.adjust(
            user_id=viewer.id,
            amount=-cost,
            reason=CurrencyTransactionType.store_purchase,
            context=f"scenario_run_boost:{prompt.id}:{uuid.uuid4().hex}",
            metadata={
                "scenario_prompt_slug": prompt.slug,
                "bonus_runs": bonus_runs,
                "feature": "scenario_demo_run_boost",
            },
            now=now,
        )

        boost = await self._demo_repo.get_user_run_boost(user_id=viewer.id, prompt_id=prompt.id)
        if boost is None:
            boost = UserScenarioRunBoost(
                user_id=viewer.id,
                prompt_id=prompt.id,
                bonus_runs_remaining=bonus_runs,
                created_at=now,
                updated_at=now,
            )
            await self._demo_repo.create_user_run_boost(boost)
        else:
            boost.bonus_runs_remaining = int(boost.bonus_runs_remaining) + bonus_runs
            await self._demo_repo.save_user_run_boost(boost)

        return ScenarioTokenBoostPurchaseRead(
            prompt_slug=prompt.slug,
            applied_bonus_runs=bonus_runs,
            bonus_runs_remaining=int(boost.bonus_runs_remaining),
            token_cost=cost,
            balance_after=int(transaction.balance_after),
            is_pro=False,
        )

    async def create_blueprint(self, *, viewer: User, body: ScenarioBlueprintWrite) -> ScenarioBlueprintRead:
        slug = _normalize_slug(body.slug)
        existing = await self._repo.get_owner_blueprint_by_slug(owner_user_id=viewer.id, slug=slug)
        if existing is not None:
            raise AppError(
                code="scenario_blueprint_slug_conflict",
                message="Blueprint slug already exists in your workspace.",
                status_code=409,
            )

        source_prompt_id = None
        if body.source_prompt_slug:
            source_prompt = await self._prompt_repo.get_by_slug(body.source_prompt_slug)
            if source_prompt is None or source_prompt.status != PromptStatus.published:
                raise NotFoundError("prompt", body.source_prompt_slug)
            source_prompt_id = source_prompt.id

        now = datetime.now(timezone.utc)
        blueprint = UserScenarioBlueprint(
            owner_user_id=viewer.id,
            source_prompt_id=source_prompt_id,
            forked_from_id=None,
            slug=slug,
            title=body.title.strip(),
            summary=body.summary.strip() if body.summary else None,
            category=body.category,
            visibility=body.visibility,
            is_published=body.visibility in {"public", "marketplace"},
            is_premium=body.is_premium,
            token_price=body.token_price if body.is_premium else None,
            input_schema=body.input_schema,
            context_text=body.context_text,
            logic_text=body.logic_text,
            output_text=body.output_text,
            run_instructions=body.run_instructions,
            usage_count=0,
            fork_count=0,
            like_count=0,
            published_at=now if body.visibility in {"public", "marketplace"} else None,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create_blueprint(blueprint)
        return _blueprint_to_read(created)

    async def patch_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
        body: ScenarioBlueprintPatchWrite,
    ) -> ScenarioBlueprintRead:
        blueprint = await self._repo.get_owner_blueprint(owner_user_id=viewer.id, blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        if body.title is not None:
            blueprint.title = body.title.strip()
        if body.summary is not None:
            blueprint.summary = body.summary.strip() or None
        if body.category is not None:
            blueprint.category = body.category
        if body.visibility is not None:
            blueprint.visibility = body.visibility
        if body.input_schema is not None:
            blueprint.input_schema = body.input_schema
        if body.context_text is not None:
            blueprint.context_text = body.context_text
        if body.logic_text is not None:
            blueprint.logic_text = body.logic_text
        if body.output_text is not None:
            blueprint.output_text = body.output_text
        if body.run_instructions is not None:
            blueprint.run_instructions = body.run_instructions
        if body.is_premium is not None:
            blueprint.is_premium = body.is_premium
            if not body.is_premium:
                blueprint.token_price = None
        if body.token_price is not None and blueprint.is_premium:
            blueprint.token_price = int(body.token_price)

        blueprint.updated_at = datetime.now(timezone.utc)
        saved = await self._repo.save_blueprint(blueprint)
        return _blueprint_to_read(saved)

    async def publish_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
    ) -> ScenarioBlueprintPublishRead:
        blueprint = await self._repo.get_owner_blueprint(owner_user_id=viewer.id, blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        now = datetime.now(timezone.utc)
        blueprint.is_published = True
        if blueprint.visibility == "private":
            blueprint.visibility = "marketplace"
        blueprint.published_at = now
        blueprint.updated_at = now
        saved = await self._repo.save_blueprint(blueprint)

        reward_applied = await self._apply_creator_reward(
            event_key=f"scenario_blueprint_publish:{saved.id}",
            recipient_user_id=viewer.id,
            blueprint_id=saved.id,
            reward_tokens=int(self._settings.scenario_creator_publish_reward_tokens),
            reason="publish",
        )

        return ScenarioBlueprintPublishRead(
            blueprint=_blueprint_to_read(saved),
            creator_reward_tokens=int(self._settings.scenario_creator_publish_reward_tokens),
            creator_reward_applied=reward_applied,
        )

    async def list_my_blueprints(self, *, viewer: User) -> list[ScenarioBlueprintRead]:
        rows = await self._repo.list_owner_blueprints(owner_user_id=viewer.id)
        return [_blueprint_to_read(row) for row in rows]

    async def list_marketplace_blueprints(self, *, limit: int = 24) -> list[ScenarioBlueprintRead]:
        rows = await self._repo.list_public_blueprints(limit=limit)
        return [_blueprint_to_read(row) for row in rows]

    async def fork_marketplace_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
    ) -> ScenarioMarketplaceForkRead:
        source = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if source is None or not source.is_published or source.visibility not in {"public", "marketplace"}:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        token_spent = 0
        balance_after: int | None = None
        if source.is_premium and source.token_price and source.owner_user_id != viewer.id:
            token_spent = int(source.token_price)
            await self._wallet.ensure_wallet(viewer.id)
            transaction = await self._wallet.adjust(
                user_id=viewer.id,
                amount=-token_spent,
                reason=CurrencyTransactionType.store_purchase,
                context=f"scenario_marketplace_fork:{source.id}:{uuid.uuid4().hex}",
                metadata={"source_blueprint_id": str(source.id)},
                now=datetime.now(timezone.utc),
            )
            balance_after = int(transaction.balance_after)

        fork_slug = _normalize_slug(f"{source.slug}-fork-{uuid.uuid4().hex[:6]}")
        now = datetime.now(timezone.utc)
        forked = UserScenarioBlueprint(
            owner_user_id=viewer.id,
            source_prompt_id=source.source_prompt_id,
            forked_from_id=source.id,
            slug=fork_slug,
            title=f"{source.title} (Fork)",
            summary=source.summary,
            category=source.category,
            visibility="private",
            is_published=False,
            is_premium=False,
            token_price=None,
            input_schema=source.input_schema,
            context_text=source.context_text,
            logic_text=source.logic_text,
            output_text=source.output_text,
            run_instructions=source.run_instructions,
            usage_count=0,
            fork_count=0,
            like_count=0,
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create_blueprint(forked)
        source.fork_count = int(source.fork_count) + 1
        await self._repo.save_blueprint(source)

        reward_applied = False
        if source.owner_user_id != viewer.id:
            reward_applied = await self._apply_creator_reward(
                event_key=f"scenario_blueprint_fork:{source.id}:{viewer.id}",
                recipient_user_id=source.owner_user_id,
                blueprint_id=source.id,
                reward_tokens=int(self._settings.scenario_creator_fork_reward_tokens),
                reason="fork",
            )

        return ScenarioMarketplaceForkRead(
            source_blueprint_id=source.id,
            forked_blueprint=_blueprint_to_read(created),
            token_spent=token_spent,
            balance_after=balance_after,
            creator_reward_applied=reward_applied,
        )

    async def like_marketplace_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
    ) -> ScenarioBlueprintRead:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None or not blueprint.is_published:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        event_key = f"scenario_blueprint_like:{blueprint.id}:{viewer.id}"
        existing = await self._repo.get_creator_reward_event(event_key=event_key)
        if existing is not None:
            return _blueprint_to_read(blueprint)

        blueprint.like_count = int(blueprint.like_count) + 1
        await self._repo.save_blueprint(blueprint)

        reward_tokens = int(self._settings.scenario_creator_like_reward_tokens)
        if reward_tokens > 0 and blueprint.owner_user_id != viewer.id:
            await self._apply_creator_reward(
                event_key=event_key,
                recipient_user_id=blueprint.owner_user_id,
                blueprint_id=blueprint.id,
                reward_tokens=reward_tokens,
                reason="like",
            )
        else:
            await self._repo.create_creator_reward_event(
                ScenarioCreatorRewardEvent(
                    event_key=event_key,
                    recipient_user_id=blueprint.owner_user_id,
                    blueprint_id=blueprint.id,
                    reward_tokens=0,
                    reason="like",
                    created_at=datetime.now(timezone.utc),
                )
            )
        return _blueprint_to_read(blueprint)

    async def share_blueprint_with_member(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
        body: ScenarioBlueprintShareWrite,
    ) -> ScenarioBlueprintShareRead:
        blueprint = await self._repo.get_owner_blueprint(owner_user_id=viewer.id, blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        member = await self._user_repo.get_by_email(body.member_email.strip().lower())
        if member is None:
            raise NotFoundError("user", body.member_email)
        if member.id == viewer.id:
            raise AppError(
                code="invalid_team_share",
                message="You already own this blueprint.",
                status_code=400,
            )

        existing = await self._repo.get_blueprint_share(blueprint_id=blueprint.id, member_user_id=member.id)
        if existing is not None:
            existing.can_edit = body.can_edit
            saved = await self._repo.save_blueprint_share(existing)
            return ScenarioBlueprintShareRead.model_validate(saved)

        created = await self._repo.create_blueprint_share(
            UserScenarioBlueprintShare(
                blueprint_id=blueprint.id,
                owner_user_id=viewer.id,
                member_user_id=member.id,
                can_edit=body.can_edit,
                created_at=datetime.now(timezone.utc),
            )
        )
        return ScenarioBlueprintShareRead.model_validate(created)

    async def list_team_shared_blueprints(self, *, viewer: User) -> list[ScenarioBlueprintRead]:
        rows = await self._repo.list_shared_blueprints_for_member(member_user_id=viewer.id)
        return [_blueprint_to_read(row) for row in rows]

    async def create_workflow(self, *, viewer: User, body: ScenarioWorkflowWrite) -> ScenarioWorkflowRead:
        steps = await self._repo.list_blueprints_by_ids(body.step_blueprint_ids)
        step_by_id = {item.id: item for item in steps}

        for step_id in body.step_blueprint_ids:
            step = step_by_id.get(step_id)
            if step is None:
                raise NotFoundError("scenario_blueprint", str(step_id))
            if step.owner_user_id != viewer.id and not step.is_published:
                raise AppError(
                    code="workflow_step_access_denied",
                    message="Workflow can include only your or published blueprints.",
                    status_code=403,
                )

        now = datetime.now(timezone.utc)
        workflow = UserScenarioWorkflow(
            owner_user_id=viewer.id,
            name=body.name.strip(),
            description=body.description.strip() if body.description else None,
            visibility=body.visibility,
            step_blueprint_ids=[str(step_id) for step_id in body.step_blueprint_ids],
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create_workflow(workflow)
        return _workflow_to_read(created)

    async def list_my_workflows(self, *, viewer: User) -> list[ScenarioWorkflowRead]:
        rows = await self._repo.list_owner_workflows(owner_user_id=viewer.id)
        return [_workflow_to_read(row) for row in rows]

    async def start_workflow_run(
        self,
        *,
        viewer: User,
        workflow_id: uuid.UUID,
        body: ScenarioWorkflowRunStartWrite,
    ) -> ScenarioWorkflowRunRead:
        workflow = await self._repo.get_owner_workflow(owner_user_id=viewer.id, workflow_id=workflow_id)
        if workflow is None:
            raise NotFoundError("scenario_workflow", str(workflow_id))

        now = datetime.now(timezone.utc)
        run = UserScenarioWorkflowRun(
            workflow_id=workflow.id,
            actor_user_id=viewer.id,
            guest_id=None,
            status="in_progress",
            current_step=0,
            completed_steps=0,
            context_json=body.context or {},
            started_at=now,
            last_active_at=now,
            completed_at=None,
        )
        created = await self._repo.create_workflow_run(run)
        return self._to_workflow_run_read(created, workflow)

    async def advance_workflow_run(
        self,
        *,
        viewer: User,
        run_id: uuid.UUID,
    ) -> ScenarioWorkflowRunAdvanceRead:
        run = await self._repo.get_workflow_run_by_id(run_id=run_id)
        if run is None:
            raise NotFoundError("scenario_workflow_run", str(run_id))
        if run.actor_user_id != viewer.id:
            raise AppError(
                code="workflow_run_forbidden",
                message="This workflow run does not belong to your account.",
                status_code=403,
            )

        workflow = await self._repo.get_owner_workflow(owner_user_id=viewer.id, workflow_id=run.workflow_id)
        if workflow is None:
            raise NotFoundError("scenario_workflow", str(run.workflow_id))

        total_steps = len(workflow.step_blueprint_ids)
        run.completed_steps = min(int(run.completed_steps) + 1, total_steps)
        run.current_step = min(int(run.current_step) + 1, total_steps)
        run.last_active_at = datetime.now(timezone.utc)
        if int(run.current_step) >= total_steps:
            run.status = "completed"
            run.completed_at = run.last_active_at
        saved = await self._repo.save_workflow_run(run)
        run_read = self._to_workflow_run_read(saved, workflow)
        return ScenarioWorkflowRunAdvanceRead(
            run=run_read,
            is_completed=run_read.status == "completed",
            next_blueprint_id=run_read.next_blueprint_id,
        )

    def _to_workflow_run_read(
        self,
        run: UserScenarioWorkflowRun,
        workflow: UserScenarioWorkflow,
    ) -> ScenarioWorkflowRunRead:
        total_steps = len(workflow.step_blueprint_ids)
        next_blueprint_id: uuid.UUID | None = None
        if int(run.current_step) < total_steps:
            try:
                next_blueprint_id = uuid.UUID(workflow.step_blueprint_ids[int(run.current_step)])
            except Exception:
                next_blueprint_id = None
        return ScenarioWorkflowRunRead(
            id=run.id,
            workflow_id=run.workflow_id,
            status=run.status,
            current_step=int(run.current_step),
            completed_steps=int(run.completed_steps),
            total_steps=total_steps,
            next_blueprint_id=next_blueprint_id,
            completed_at=run.completed_at,
            last_active_at=run.last_active_at,
        )

    async def create_showcase(
        self,
        *,
        viewer: User | None,
        body: ScenarioShowcaseCreateWrite,
    ) -> ScenarioShowcaseRead:
        share_id = body.share_id.strip() if body.share_id else f"showcase-{uuid.uuid4().hex}"
        if await self._repo.get_showcase_by_share_id(share_id=share_id):
            raise AppError(
                code="showcase_share_id_conflict",
                message="Showcase id already exists.",
                status_code=409,
            )

        blueprint_id = body.blueprint_id
        if blueprint_id is not None:
            blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
            if blueprint is None:
                raise NotFoundError("scenario_blueprint", str(blueprint_id))
            if blueprint.visibility not in {"public", "marketplace"} and (
                viewer is None or blueprint.owner_user_id != viewer.id
            ):
                raise AppError(
                    code="showcase_blueprint_forbidden",
                    message="You do not have access to this blueprint showcase.",
                    status_code=403,
                )

        row = ScenarioOutputShowcase(
            share_id=share_id,
            author_user_id=viewer.id if viewer is not None else None,
            prompt_slug=body.prompt_slug,
            blueprint_id=blueprint_id,
            title=body.title.strip(),
            excerpt=body.excerpt.strip(),
            output_preview=body.output_preview.strip(),
            visibility=body.visibility,
            upvotes=0,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create_showcase(row)
        return _showcase_to_read(created)

    async def list_showcase(self, *, limit: int = 24) -> list[ScenarioShowcaseRead]:
        rows = await self._repo.list_public_showcase(limit=limit)
        return [_showcase_to_read(row) for row in rows]

    async def upvote_showcase(
        self,
        *,
        viewer: User,
        share_id: str,
    ) -> ScenarioShowcaseRead:
        showcase = await self._repo.get_showcase_by_share_id(share_id=share_id)
        if showcase is None:
            raise NotFoundError("scenario_showcase", share_id)

        event_key = f"scenario_showcase_like:{share_id}:{viewer.id}"
        existing = await self._repo.get_creator_reward_event(event_key=event_key)
        if existing is not None:
            return _showcase_to_read(showcase)

        showcase.upvotes = int(showcase.upvotes) + 1
        await self._repo.save_showcase(showcase)

        reward_tokens = int(self._settings.scenario_creator_like_reward_tokens)
        if reward_tokens > 0 and showcase.author_user_id and showcase.author_user_id != viewer.id:
            await self._apply_creator_reward(
                event_key=event_key,
                recipient_user_id=showcase.author_user_id,
                blueprint_id=showcase.blueprint_id,
                reward_tokens=reward_tokens,
                reason="showcase_like",
            )
        else:
            await self._repo.create_creator_reward_event(
                ScenarioCreatorRewardEvent(
                    event_key=event_key,
                    recipient_user_id=showcase.author_user_id or viewer.id,
                    blueprint_id=showcase.blueprint_id,
                    reward_tokens=0,
                    reason="showcase_like",
                    created_at=datetime.now(timezone.utc),
                )
            )
        return _showcase_to_read(showcase)

    async def recommend_next(
        self,
        *,
        source_prompt_slug: str | None,
        recommended: list[PromptListItem],
        chains: list[ScenarioChainRead],
    ) -> ScenarioNextStepRead | None:
        if source_prompt_slug:
            for chain in chains:
                for index, step in enumerate(chain.steps):
                    if step.prompt_slug != source_prompt_slug:
                        continue
                    if index + 1 >= len(chain.steps):
                        break
                    return ScenarioNextStepRead(
                        source_prompt_slug=source_prompt_slug,
                        next_prompt_slug=chain.steps[index + 1].prompt_slug,
                        reason=f"Next step in chain {chain.title}",
                        confidence=0.9,
                    )
        for candidate in recommended:
            if candidate.slug == source_prompt_slug:
                continue
            return ScenarioNextStepRead(
                source_prompt_slug=source_prompt_slug,
                next_prompt_slug=candidate.slug,
                reason="Behavior-based recommendation",
                confidence=0.75,
            )
        return None

    async def _apply_creator_reward(
        self,
        *,
        event_key: str,
        recipient_user_id: uuid.UUID,
        blueprint_id: uuid.UUID | None,
        reward_tokens: int,
        reason: str,
    ) -> bool:
        existing = await self._repo.get_creator_reward_event(event_key=event_key)
        if existing is not None:
            return False

        now = datetime.now(timezone.utc)
        if reward_tokens > 0:
            await self._wallet.ensure_wallet(recipient_user_id)
            await self._wallet.adjust(
                user_id=recipient_user_id,
                amount=reward_tokens,
                reason=CurrencyTransactionType.surprise_reward,
                context=f"scenario_creator_reward:{event_key}",
                metadata={
                    "reason": reason,
                    "event_key": event_key,
                    "blueprint_id": str(blueprint_id) if blueprint_id else None,
                },
                now=now,
            )

        await self._repo.create_creator_reward_event(
            ScenarioCreatorRewardEvent(
                event_key=event_key,
                recipient_user_id=recipient_user_id,
                blueprint_id=blueprint_id,
                reward_tokens=reward_tokens,
                reason=reason,
                created_at=now,
            )
        )
        return True

    async def build_pack_prompts(self, *, prompt_slugs: list[str]) -> list[PromptListItem]:
        prompts: list[PromptListItem] = []
        for slug in prompt_slugs:
            row = await self._prompt_repo.get_by_slug(slug)
            if row is None or row.status != PromptStatus.published:
                continue
            prompts.append(PromptListItem.model_validate(to_list_item(row)))
        return prompts
