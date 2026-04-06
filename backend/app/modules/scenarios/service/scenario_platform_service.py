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
    ScenarioBlueprintComment,
    ScenarioBlueprintRating,
    ScenarioBlueprintSave,
    ScenarioBlueprintVersion,
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
    ScenarioBlueprintCommentRead,
    ScenarioBlueprintCommentWrite,
    ScenarioBlueprintLineageNodeRead,
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


def _normalize_tags(raw_tags: object) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    tags: list[str] = []
    for item in raw_tags:
        if not isinstance(item, str):
            continue
        clean = item.strip().lower()
        if not clean:
            continue
        if clean not in tags:
            tags.append(clean)
        if len(tags) >= 20:
            break
    return tags


def _resolve_monetization_mode(row: UserScenarioBlueprint) -> str:
    mode = (row.monetization_mode or "").strip().lower()
    if mode in {"free", "pro_only", "paid"}:
        return mode
    if bool(row.is_premium):
        return "paid" if row.token_price else "pro_only"
    return "free"


def _blueprint_snapshot(row: UserScenarioBlueprint) -> dict[str, object]:
    return {
        "id": str(row.id),
        "owner_user_id": str(row.owner_user_id),
        "slug": row.slug,
        "title": row.title,
        "summary": row.summary,
        "category": row.category,
        "tags": _normalize_tags(row.tags),
        "metadata": row.metadata_json if isinstance(row.metadata_json, dict) else None,
        "visibility": row.visibility,
        "monetization_mode": _resolve_monetization_mode(row),
        "autonomous_mode": bool(getattr(row, "autonomous_mode", False)),
        "autonomous_stage": str(getattr(row, "autonomous_stage", "manual") or "manual"),
        "autonomous_quality_score": float(getattr(row, "autonomous_quality_score", 0.0) or 0.0),
        "autonomous_target_segment": getattr(row, "autonomous_target_segment", None),
        "autonomous_last_iteration_at": (
            getattr(row, "autonomous_last_iteration_at", None).isoformat()
            if getattr(row, "autonomous_last_iteration_at", None)
            else None
        ),
        "is_published": bool(row.is_published),
        "is_premium": bool(row.is_premium),
        "token_price": int(row.token_price) if row.token_price is not None else None,
        "input_schema": row.input_schema,
        "context_text": row.context_text,
        "logic_text": row.logic_text,
        "output_text": row.output_text,
        "run_instructions": row.run_instructions,
        "version_number": int(row.version_number or 1),
        "forked_from_id": str(row.forked_from_id) if row.forked_from_id else None,
        "root_blueprint_id": str(row.root_blueprint_id) if row.root_blueprint_id else str(row.id),
        "stats": {
            "usage_count": int(row.usage_count or 0),
            "run_count": int(row.run_count or 0),
            "completion_count": int(row.completion_count or 0),
            "save_count": int(row.save_count or 0),
            "fork_count": int(row.fork_count or 0),
            "like_count": int(row.like_count or 0),
            "comment_count": int(row.comment_count or 0),
            "rating_average": float(row.rating_average or 0.0),
            "rating_count": int(row.rating_count or 0),
        },
    }


def _blueprint_to_read(
    row: UserScenarioBlueprint,
    *,
    author_display_name: str | None = None,
) -> ScenarioBlueprintRead:
    return ScenarioBlueprintRead(
        id=row.id,
        owner_user_id=row.owner_user_id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        category=row.category,
        tags=_normalize_tags(row.tags),
        metadata=row.metadata_json if isinstance(row.metadata_json, dict) else None,
        author_display_name=author_display_name,
        visibility=row.visibility,
        monetization_mode=_resolve_monetization_mode(row),
        autonomous_mode=bool(getattr(row, "autonomous_mode", False)),
        autonomous_stage=str(getattr(row, "autonomous_stage", "manual") or "manual"),
        autonomous_quality_score=float(getattr(row, "autonomous_quality_score", 0.0) or 0.0),
        autonomous_target_segment=getattr(row, "autonomous_target_segment", None),
        autonomous_last_iteration_at=getattr(row, "autonomous_last_iteration_at", None),
        is_published=bool(row.is_published),
        is_premium=bool(row.is_premium),
        token_price=int(row.token_price) if row.token_price is not None else None,
        input_schema=row.input_schema,
        context_text=row.context_text,
        logic_text=row.logic_text,
        output_text=row.output_text,
        run_instructions=row.run_instructions,
        usage_count=int(row.usage_count or 0),
        run_count=int(row.run_count or 0),
        completion_count=int(row.completion_count or 0),
        save_count=int(row.save_count or 0),
        fork_count=int(row.fork_count or 0),
        like_count=int(row.like_count or 0),
        comment_count=int(row.comment_count or 0),
        rating_average=float(row.rating_average or 0.0),
        rating_count=int(row.rating_count or 0),
        version_number=int(row.version_number or 1),
        forked_from_id=row.forked_from_id,
        root_blueprint_id=row.root_blueprint_id or row.id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
    )


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

    async def _owner_name_map(self, owner_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
        mapping: dict[uuid.UUID, str] = {}
        for owner_id in owner_ids:
            user = await self._user_repo.get_by_id(owner_id)
            if user is None:
                continue
            if user.display_name and user.display_name.strip():
                mapping[owner_id] = user.display_name.strip()
                continue
            username = (user.username or "").strip()
            mapping[owner_id] = username or f"user-{str(owner_id)[:8]}"
        return mapping

    async def _to_blueprint_reads(self, rows: list[UserScenarioBlueprint]) -> list[ScenarioBlueprintRead]:
        owner_map = await self._owner_name_map({row.owner_user_id for row in rows})
        return [
            _blueprint_to_read(row, author_display_name=owner_map.get(row.owner_user_id))
            for row in rows
        ]

    @staticmethod
    def _normalize_visibility_and_monetization(
        *,
        visibility: str,
        monetization_mode: str | None,
        is_premium: bool | None,
        token_price: int | None,
    ) -> tuple[str, str, bool, int | None]:
        normalized_visibility = visibility.strip().lower()
        normalized_mode = (monetization_mode or "").strip().lower()

        if normalized_mode not in {"free", "pro_only", "paid"}:
            if is_premium:
                normalized_mode = "paid" if token_price else "pro_only"
            elif normalized_visibility == "premium":
                normalized_mode = "paid" if token_price else "pro_only"
            else:
                normalized_mode = "free"

        if normalized_visibility == "premium" and normalized_mode == "free":
            normalized_mode = "paid" if token_price else "pro_only"

        normalized_token_price = int(token_price) if token_price is not None else None
        normalized_is_premium = normalized_mode in {"pro_only", "paid"}
        if normalized_mode == "free":
            normalized_token_price = None
        if normalized_mode == "pro_only":
            normalized_token_price = None
        if normalized_mode == "paid" and (normalized_token_price is None or normalized_token_price <= 0):
            raise AppError(
                code="invalid_monetization_price",
                message="Paid scenarios require a positive token price.",
                status_code=400,
            )

        if normalized_visibility == "premium":
            normalized_visibility = "marketplace"
        if normalized_visibility not in {"private", "team", "public", "marketplace"}:
            raise AppError(
                code="invalid_visibility",
                message="Visibility must be private, team, public, or premium.",
                status_code=400,
            )
        return (
            normalized_visibility,
            normalized_mode,
            normalized_is_premium,
            normalized_token_price,
        )

    async def _record_blueprint_version(
        self,
        *,
        blueprint: UserScenarioBlueprint,
        actor_user_id: uuid.UUID | None,
        change_note: str,
    ) -> None:
        await self._repo.create_blueprint_version(
            ScenarioBlueprintVersion(
                blueprint_id=blueprint.id,
                version_number=int(blueprint.version_number or 1),
                snapshot_json=_blueprint_snapshot(blueprint),
                change_note=change_note,
                created_by_user_id=actor_user_id,
                created_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _completion_rate(blueprint: UserScenarioBlueprint) -> float:
        runs = max(int(blueprint.run_count or 0), 1)
        return min(1.0, max(0.0, float(blueprint.completion_count or 0) / float(runs)))

    def _trending_score(self, blueprint: UserScenarioBlueprint, *, now: datetime) -> float:
        published_at = blueprint.published_at or blueprint.created_at or now
        age_hours = max((now - published_at).total_seconds() / 3600.0, 1.0)
        growth_signal = (
            float(blueprint.run_count or 0) * 1.5
            + float(blueprint.save_count or 0) * 3.0
            + float(blueprint.fork_count or 0) * 4.0
            + float(blueprint.like_count or 0) * 1.2
            + float(blueprint.comment_count or 0) * 2.2
            + float(blueprint.rating_average or 0.0) * float(blueprint.rating_count or 0)
        )
        return growth_signal / age_hours

    def _best_score(self, blueprint: UserScenarioBlueprint) -> float:
        completion_rate = self._completion_rate(blueprint)
        return (
            completion_rate * 70.0
            + float(blueprint.rating_average or 0.0) * 12.0
            + float(blueprint.save_count or 0) * 2.0
            + float(blueprint.run_count or 0) * 0.3
        )

    def _top_score(self, blueprint: UserScenarioBlueprint) -> float:
        return (
            float(blueprint.usage_count or 0) * 1.0
            + float(blueprint.run_count or 0) * 1.5
            + float(blueprint.save_count or 0) * 2.5
            + float(blueprint.fork_count or 0) * 4.0
            + float(blueprint.like_count or 0) * 1.4
        )

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

        visibility, monetization_mode, is_premium, token_price = self._normalize_visibility_and_monetization(
            visibility=body.visibility,
            monetization_mode=body.monetization_mode,
            is_premium=body.is_premium,
            token_price=body.token_price,
        )
        now = datetime.now(timezone.utc)
        blueprint = UserScenarioBlueprint(
            owner_user_id=viewer.id,
            source_prompt_id=source_prompt_id,
            forked_from_id=None,
            root_blueprint_id=None,
            slug=slug,
            title=body.title.strip(),
            summary=body.summary.strip() if body.summary else None,
            category=body.category,
            tags=_normalize_tags(body.tags),
            metadata_json=body.metadata if isinstance(body.metadata, dict) else None,
            visibility=visibility,
            is_published=visibility in {"public", "marketplace"},
            is_premium=is_premium,
            monetization_mode=monetization_mode,
            token_price=token_price,
            input_schema=body.input_schema,
            context_text=body.context_text,
            logic_text=body.logic_text,
            output_text=body.output_text,
            run_instructions=body.run_instructions,
            usage_count=0,
            run_count=0,
            completion_count=0,
            save_count=0,
            fork_count=0,
            like_count=0,
            comment_count=0,
            rating_average=0.0,
            rating_count=0,
            version_number=1,
            published_at=now if visibility in {"public", "marketplace"} else None,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create_blueprint(blueprint)
        created.root_blueprint_id = created.id
        await self._repo.save_blueprint(created)
        await self._record_blueprint_version(
            blueprint=created,
            actor_user_id=viewer.id,
            change_note="created",
        )
        owner_map = await self._owner_name_map({created.owner_user_id})
        return _blueprint_to_read(created, author_display_name=owner_map.get(created.owner_user_id))

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
        if body.tags is not None:
            blueprint.tags = _normalize_tags(body.tags)
        if body.metadata is not None:
            blueprint.metadata_json = body.metadata if isinstance(body.metadata, dict) else None
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

        visibility = body.visibility or blueprint.visibility
        monetization_mode = body.monetization_mode or blueprint.monetization_mode
        is_premium = body.is_premium if body.is_premium is not None else blueprint.is_premium
        token_price = body.token_price if body.token_price is not None else blueprint.token_price
        (
            blueprint.visibility,
            blueprint.monetization_mode,
            blueprint.is_premium,
            blueprint.token_price,
        ) = self._normalize_visibility_and_monetization(
            visibility=visibility,
            monetization_mode=monetization_mode,
            is_premium=is_premium,
            token_price=token_price,
        )
        blueprint.is_published = blueprint.visibility in {"public", "marketplace"} or bool(blueprint.is_published)

        blueprint.version_number = int(blueprint.version_number or 1) + 1
        blueprint.updated_at = datetime.now(timezone.utc)
        saved = await self._repo.save_blueprint(blueprint)
        await self._record_blueprint_version(
            blueprint=saved,
            actor_user_id=viewer.id,
            change_note="edited",
        )
        owner_map = await self._owner_name_map({saved.owner_user_id})
        return _blueprint_to_read(saved, author_display_name=owner_map.get(saved.owner_user_id))

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
        if blueprint.visibility == "premium":
            blueprint.visibility = "marketplace"
        blueprint.published_at = now
        blueprint.version_number = int(blueprint.version_number or 1) + 1
        blueprint.updated_at = now
        saved = await self._repo.save_blueprint(blueprint)
        await self._record_blueprint_version(
            blueprint=saved,
            actor_user_id=viewer.id,
            change_note="published",
        )

        reward_applied = await self._apply_creator_reward(
            event_key=f"scenario_blueprint_publish:{saved.id}",
            recipient_user_id=viewer.id,
            blueprint_id=saved.id,
            reward_tokens=int(self._settings.scenario_creator_publish_reward_tokens),
            reason="publish",
        )

        owner_map = await self._owner_name_map({saved.owner_user_id})
        return ScenarioBlueprintPublishRead(
            blueprint=_blueprint_to_read(saved, author_display_name=owner_map.get(saved.owner_user_id)),
            creator_reward_tokens=int(self._settings.scenario_creator_publish_reward_tokens),
            creator_reward_applied=reward_applied,
        )

    async def list_my_blueprints(self, *, viewer: User) -> list[ScenarioBlueprintRead]:
        rows = await self._repo.list_owner_blueprints(owner_user_id=viewer.id)
        return await self._to_blueprint_reads(list(rows))

    async def list_marketplace_blueprints(
        self,
        *,
        limit: int = 24,
        section: str = "trending",
        search: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        viewer: User | None = None,
    ) -> list[ScenarioBlueprintRead]:
        fetch_limit = max(limit * 6, 60)
        rows = list(
            await self._repo.list_public_blueprints_filtered(
                limit=fetch_limit,
                search=search,
                category=category,
            )
        )

        normalized_tags = _normalize_tags(tags or [])
        if normalized_tags:
            tag_set = set(normalized_tags)
            rows = [row for row in rows if tag_set.intersection(set(_normalize_tags(row.tags)))]
        rows = [
            row
            for row in rows
            if not (
                bool(getattr(row, "autonomous_mode", False))
                and str(getattr(row, "autonomous_stage", "manual") or "manual") == "retired"
            )
        ]

        now = datetime.now(timezone.utc)
        section_key = (section or "trending").strip().lower()
        if section_key == "new":
            rows.sort(key=lambda item: item.published_at or item.created_at, reverse=True)
        elif section_key == "top":
            rows.sort(key=lambda item: self._top_score(item), reverse=True)
        elif section_key == "best":
            rows.sort(key=lambda item: self._best_score(item), reverse=True)
        elif section_key == "personalized":
            preferred_categories: set[str] = set()
            if viewer is not None:
                my_rows = await self._repo.list_owner_blueprints(owner_user_id=viewer.id)
                preferred_categories = {item.category for item in my_rows if item.category}
            rows.sort(
                key=lambda item: (
                    0 if (preferred_categories and item.category in preferred_categories) else 1,
                    -self._trending_score(item, now=now),
                )
            )
        else:
            rows.sort(key=lambda item: self._trending_score(item, now=now), reverse=True)

        return await self._to_blueprint_reads(rows[:limit])

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
        monetization_mode = _resolve_monetization_mode(source)
        if source.owner_user_id != viewer.id:
            if monetization_mode == "pro_only" and viewer.plan_tier == PlanTier.free:
                raise AppError(
                    code="scenario_blueprint_pro_required",
                    message="Upgrade to Pro to remix this scenario.",
                    status_code=402,
                )
            if monetization_mode == "paid":
                price = int(source.token_price or 0)
                if price <= 0:
                    raise AppError(
                        code="scenario_blueprint_paid_price_missing",
                        message="This paid scenario is temporarily unavailable.",
                        status_code=400,
                    )
                token_spent = price
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
            root_blueprint_id=source.root_blueprint_id or source.id,
            slug=fork_slug,
            title=f"{source.title} (Fork)",
            summary=source.summary,
            category=source.category,
            tags=_normalize_tags(source.tags),
            metadata_json=source.metadata_json if isinstance(source.metadata_json, dict) else None,
            visibility="private",
            is_published=False,
            is_premium=False,
            monetization_mode="free",
            token_price=None,
            input_schema=source.input_schema,
            context_text=source.context_text,
            logic_text=source.logic_text,
            output_text=source.output_text,
            run_instructions=source.run_instructions,
            usage_count=0,
            run_count=0,
            completion_count=0,
            save_count=0,
            fork_count=0,
            like_count=0,
            comment_count=0,
            rating_average=0.0,
            rating_count=0,
            version_number=1,
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create_blueprint(forked)
        await self._record_blueprint_version(
            blueprint=created,
            actor_user_id=viewer.id,
            change_note="remix_created",
        )
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

        owner_map = await self._owner_name_map({created.owner_user_id})
        return ScenarioMarketplaceForkRead(
            source_blueprint_id=source.id,
            forked_blueprint=_blueprint_to_read(created, author_display_name=owner_map.get(created.owner_user_id)),
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
            owner_map = await self._owner_name_map({blueprint.owner_user_id})
            return _blueprint_to_read(blueprint, author_display_name=owner_map.get(blueprint.owner_user_id))

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
        owner_map = await self._owner_name_map({blueprint.owner_user_id})
        return _blueprint_to_read(blueprint, author_display_name=owner_map.get(blueprint.owner_user_id))

    async def remix_marketplace_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
    ) -> ScenarioMarketplaceForkRead:
        return await self.fork_marketplace_blueprint(viewer=viewer, blueprint_id=blueprint_id)

    async def list_blueprint_versions(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
        limit: int = 40,
    ) -> list[ScenarioBlueprintVersionRead]:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))
        if blueprint.owner_user_id != viewer.id and blueprint.visibility not in {"public", "marketplace"}:
            raise AppError(
                code="scenario_blueprint_versions_forbidden",
                message="You do not have access to this scenario version history.",
                status_code=403,
            )
        rows = await self._repo.list_blueprint_versions(blueprint_id=blueprint_id, limit=limit)
        return [ScenarioBlueprintVersionRead.model_validate(row) for row in rows]

    async def get_blueprint_lineage(
        self,
        *,
        viewer: User | None,
        blueprint_id: uuid.UUID,
    ) -> ScenarioBlueprintLineageRead:
        current = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if current is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))
        if current.visibility not in {"public", "marketplace"} and (viewer is None or viewer.id != current.owner_user_id):
            raise AppError(
                code="scenario_blueprint_lineage_forbidden",
                message="You do not have access to this scenario lineage.",
                status_code=403,
            )

        chain_rows: list[UserScenarioBlueprint] = []
        cursor = current
        visited: set[uuid.UUID] = set()
        while cursor is not None and cursor.id not in visited:
            chain_rows.append(cursor)
            visited.add(cursor.id)
            if cursor.forked_from_id is None:
                break
            cursor = await self._repo.get_blueprint_by_id(blueprint_id=cursor.forked_from_id)
        chain_rows.reverse()
        root_id = chain_rows[0].id if chain_rows else current.id

        children_rows = await self._repo.list_blueprints_by_root(root_blueprint_id=root_id, limit=120)
        chain_ids = {row.id for row in chain_rows}
        children = [
            ScenarioBlueprintLineageNodeRead.model_validate(row)
            for row in children_rows
            if row.id not in chain_ids and row.visibility in {"public", "marketplace"}
        ]
        chain = [ScenarioBlueprintLineageNodeRead.model_validate(row) for row in chain_rows]
        return ScenarioBlueprintLineageRead(root_blueprint_id=root_id, chain=chain, children=children[:60])

    async def list_blueprint_comments(
        self,
        *,
        viewer: User | None,
        blueprint_id: uuid.UUID,
        limit: int = 40,
    ) -> list[ScenarioBlueprintCommentRead]:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))
        if blueprint.visibility not in {"public", "marketplace"} and (viewer is None or viewer.id != blueprint.owner_user_id):
            raise AppError(
                code="scenario_blueprint_comments_forbidden",
                message="You do not have access to these comments.",
                status_code=403,
            )

        rows = await self._repo.list_blueprint_comments(blueprint_id=blueprint_id, limit=limit)
        author_map = await self._owner_name_map({row.author_user_id for row in rows if row.author_user_id})
        return [
            ScenarioBlueprintCommentRead(
                id=row.id,
                blueprint_id=row.blueprint_id,
                author_user_id=row.author_user_id,
                author_display_name=author_map.get(row.author_user_id) if row.author_user_id else None,
                body=row.body,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    async def create_blueprint_comment(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
        body: ScenarioBlueprintCommentWrite,
    ) -> ScenarioBlueprintCommentRead:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))
        if blueprint.visibility not in {"public", "marketplace"} and viewer.id != blueprint.owner_user_id:
            raise AppError(
                code="scenario_blueprint_comment_forbidden",
                message="You cannot comment on this scenario.",
                status_code=403,
            )

        now = datetime.now(timezone.utc)
        comment = await self._repo.create_blueprint_comment(
            ScenarioBlueprintComment(
                blueprint_id=blueprint.id,
                author_user_id=viewer.id,
                body=body.body.strip(),
                created_at=now,
                updated_at=now,
            )
        )
        blueprint.comment_count = await self._repo.count_blueprint_comments(blueprint_id=blueprint.id)
        blueprint.updated_at = now
        await self._repo.save_blueprint(blueprint)

        owner_map = await self._owner_name_map({viewer.id})
        return ScenarioBlueprintCommentRead(
            id=comment.id,
            blueprint_id=comment.blueprint_id,
            author_user_id=comment.author_user_id,
            author_display_name=owner_map.get(viewer.id),
            body=comment.body,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def rate_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
        body: ScenarioBlueprintRatingWrite,
    ) -> ScenarioBlueprintRatingRead:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None or not blueprint.is_published:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        row = await self._repo.get_blueprint_rating_by_user(blueprint_id=blueprint.id, user_id=viewer.id)
        now = datetime.now(timezone.utc)
        if row is None:
            row = await self._repo.create_blueprint_rating(
                ScenarioBlueprintRating(
                    blueprint_id=blueprint.id,
                    user_id=viewer.id,
                    rating=int(body.rating),
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            row.rating = int(body.rating)
            row.updated_at = now
            await self._repo.save_blueprint_rating(row)

        rating_count, rating_avg = await self._repo.count_blueprint_ratings(blueprint_id=blueprint.id)
        blueprint.rating_count = int(rating_count)
        blueprint.rating_average = float(rating_avg)
        blueprint.updated_at = now
        await self._repo.save_blueprint(blueprint)
        return ScenarioBlueprintRatingRead(
            blueprint_id=blueprint.id,
            rating=int(row.rating),
            rating_average=float(blueprint.rating_average or 0.0),
            rating_count=int(blueprint.rating_count or 0),
        )

    async def toggle_save_blueprint(
        self,
        *,
        viewer: User,
        blueprint_id: uuid.UUID,
    ) -> ScenarioBlueprintSaveRead:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None or not blueprint.is_published:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))

        existing = await self._repo.get_blueprint_save_by_user(blueprint_id=blueprint.id, user_id=viewer.id)
        now = datetime.now(timezone.utc)
        saved = False
        if existing is None:
            await self._repo.create_blueprint_save(
                ScenarioBlueprintSave(
                    blueprint_id=blueprint.id,
                    user_id=viewer.id,
                    created_at=now,
                )
            )
            saved = True
        else:
            await self._repo.delete_blueprint_save(existing)
            saved = False

        blueprint.save_count = await self._repo.count_blueprint_saves(blueprint_id=blueprint.id)
        blueprint.updated_at = now
        await self._repo.save_blueprint(blueprint)
        return ScenarioBlueprintSaveRead(
            blueprint_id=blueprint.id,
            saved=saved,
            save_count=int(blueprint.save_count or 0),
        )

    async def track_blueprint_usage(
        self,
        *,
        viewer: User | None,
        blueprint_id: uuid.UUID,
        body: ScenarioBlueprintUsageTrackWrite,
    ) -> ScenarioBlueprintUsageTrackRead:
        blueprint = await self._repo.get_blueprint_by_id(blueprint_id=blueprint_id)
        if blueprint is None or not blueprint.is_published:
            raise NotFoundError("scenario_blueprint", str(blueprint_id))
        if blueprint.visibility not in {"public", "marketplace"} and (
            viewer is None or blueprint.owner_user_id != viewer.id
        ):
            raise AppError(
                code="scenario_blueprint_usage_forbidden",
                message="You cannot track usage for this scenario.",
                status_code=403,
            )

        event = body.event
        blueprint.usage_count = int(blueprint.usage_count or 0) + 1
        if event == "run":
            blueprint.run_count = int(blueprint.run_count or 0) + 1
        elif event == "complete":
            blueprint.completion_count = int(blueprint.completion_count or 0) + 1
        blueprint.updated_at = datetime.now(timezone.utc)
        await self._repo.save_blueprint(blueprint)
        return ScenarioBlueprintUsageTrackRead(
            blueprint_id=blueprint.id,
            event=event,
            usage_count=int(blueprint.usage_count or 0),
            run_count=int(blueprint.run_count or 0),
            completion_count=int(blueprint.completion_count or 0),
        )

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
        return await self._to_blueprint_reads(list(rows))

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
