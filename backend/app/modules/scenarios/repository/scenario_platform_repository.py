from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    ScenarioAutonomyCycle,
    ScenarioAutonomyExperiment,
    ScenarioAutonomyGrowthDecision,
    ScenarioAutonomyGuardrailEvent,
    ScenarioAutonomyPersonalizationProfile,
    ScenarioBlueprintComment,
    ScenarioBlueprintRating,
    ScenarioBlueprintSave,
    ScenarioBlueprintVersion,
    ScenarioCreatorRewardEvent,
    ScenarioOutputShowcase,
    User,
    UserRole,
    UserScenarioBlueprint,
    UserScenarioBlueprintShare,
    UserScenarioWorkflow,
    UserScenarioWorkflowRun,
)


class ScenarioPlatformRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_blueprint_by_id(self, *, blueprint_id: uuid.UUID) -> UserScenarioBlueprint | None:
        result = await self._session.execute(
            select(UserScenarioBlueprint).where(UserScenarioBlueprint.id == blueprint_id)
        )
        return result.scalar_one_or_none()

    async def get_owner_blueprint(
        self,
        *,
        owner_user_id: uuid.UUID,
        blueprint_id: uuid.UUID,
    ) -> UserScenarioBlueprint | None:
        result = await self._session.execute(
            select(UserScenarioBlueprint).where(
                UserScenarioBlueprint.id == blueprint_id,
                UserScenarioBlueprint.owner_user_id == owner_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_owner_blueprint_by_slug(
        self,
        *,
        owner_user_id: uuid.UUID,
        slug: str,
    ) -> UserScenarioBlueprint | None:
        result = await self._session.execute(
            select(UserScenarioBlueprint).where(
                UserScenarioBlueprint.owner_user_id == owner_user_id,
                UserScenarioBlueprint.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def list_owner_blueprints(self, *, owner_user_id: uuid.UUID) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .where(UserScenarioBlueprint.owner_user_id == owner_user_id)
            .order_by(UserScenarioBlueprint.updated_at.desc())
        )
        return result.scalars().all()

    async def list_blueprints_by_ids(self, blueprint_ids: Sequence[uuid.UUID]) -> Sequence[UserScenarioBlueprint]:
        ids = list(dict.fromkeys(blueprint_ids))
        if not ids:
            return []
        result = await self._session.execute(
            select(UserScenarioBlueprint).where(UserScenarioBlueprint.id.in_(ids))
        )
        return result.scalars().all()

    async def list_public_blueprints(self, *, limit: int = 24) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .where(
                UserScenarioBlueprint.is_published.is_(True),
                UserScenarioBlueprint.visibility.in_(["public", "marketplace"]),
            )
            .order_by(
                UserScenarioBlueprint.like_count.desc(),
                UserScenarioBlueprint.fork_count.desc(),
                UserScenarioBlueprint.updated_at.desc(),
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def list_public_blueprints_filtered(
        self,
        *,
        limit: int = 24,
        search: str | None = None,
        category: str | None = None,
    ) -> Sequence[UserScenarioBlueprint]:
        stmt = select(UserScenarioBlueprint).where(
            UserScenarioBlueprint.is_published.is_(True),
            UserScenarioBlueprint.visibility.in_(["public", "marketplace"]),
        )
        if category:
            stmt = stmt.where(UserScenarioBlueprint.category == category)
        if search:
            needle = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(UserScenarioBlueprint.title).like(needle),
                    func.lower(UserScenarioBlueprint.slug).like(needle),
                    func.lower(func.coalesce(UserScenarioBlueprint.summary, "")).like(needle),
                )
            )
        result = await self._session.execute(
            stmt.order_by(UserScenarioBlueprint.updated_at.desc()).limit(max(limit, 1))
        )
        return result.scalars().all()

    async def list_shared_blueprints_for_member(
        self,
        *,
        member_user_id: uuid.UUID,
        limit: int = 48,
    ) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .join(
                UserScenarioBlueprintShare,
                UserScenarioBlueprintShare.blueprint_id == UserScenarioBlueprint.id,
            )
            .where(UserScenarioBlueprintShare.member_user_id == member_user_id)
            .order_by(UserScenarioBlueprint.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_blueprint(self, blueprint: UserScenarioBlueprint) -> UserScenarioBlueprint:
        self._session.add(blueprint)
        await self._session.flush()
        await self._session.refresh(blueprint)
        return blueprint

    async def save_blueprint(self, blueprint: UserScenarioBlueprint) -> UserScenarioBlueprint:
        await self._session.flush()
        await self._session.refresh(blueprint)
        return blueprint

    async def list_blueprint_children(self, *, blueprint_id: uuid.UUID, limit: int = 64) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .where(UserScenarioBlueprint.forked_from_id == blueprint_id)
            .order_by(UserScenarioBlueprint.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_blueprints_by_root(self, *, root_blueprint_id: uuid.UUID, limit: int = 256) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .where(UserScenarioBlueprint.root_blueprint_id == root_blueprint_id)
            .order_by(UserScenarioBlueprint.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_blueprint_share(
        self,
        *,
        blueprint_id: uuid.UUID,
        member_user_id: uuid.UUID,
    ) -> UserScenarioBlueprintShare | None:
        result = await self._session.execute(
            select(UserScenarioBlueprintShare).where(
                UserScenarioBlueprintShare.blueprint_id == blueprint_id,
                UserScenarioBlueprintShare.member_user_id == member_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_blueprint_share(self, share: UserScenarioBlueprintShare) -> UserScenarioBlueprintShare:
        self._session.add(share)
        await self._session.flush()
        await self._session.refresh(share)
        return share

    async def save_blueprint_share(self, share: UserScenarioBlueprintShare) -> UserScenarioBlueprintShare:
        await self._session.flush()
        await self._session.refresh(share)
        return share

    async def list_blueprint_shares(self, *, blueprint_id: uuid.UUID) -> Sequence[UserScenarioBlueprintShare]:
        result = await self._session.execute(
            select(UserScenarioBlueprintShare)
            .where(UserScenarioBlueprintShare.blueprint_id == blueprint_id)
            .order_by(UserScenarioBlueprintShare.created_at.asc())
        )
        return result.scalars().all()

    async def create_blueprint_version(self, version: ScenarioBlueprintVersion) -> ScenarioBlueprintVersion:
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def list_blueprint_versions(
        self,
        *,
        blueprint_id: uuid.UUID,
        limit: int = 40,
    ) -> Sequence[ScenarioBlueprintVersion]:
        result = await self._session.execute(
            select(ScenarioBlueprintVersion)
            .where(ScenarioBlueprintVersion.blueprint_id == blueprint_id)
            .order_by(ScenarioBlueprintVersion.version_number.desc(), ScenarioBlueprintVersion.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_blueprint_rating_by_user(
        self,
        *,
        blueprint_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ScenarioBlueprintRating | None:
        result = await self._session.execute(
            select(ScenarioBlueprintRating).where(
                ScenarioBlueprintRating.blueprint_id == blueprint_id,
                ScenarioBlueprintRating.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_blueprint_rating(self, rating: ScenarioBlueprintRating) -> ScenarioBlueprintRating:
        self._session.add(rating)
        await self._session.flush()
        await self._session.refresh(rating)
        return rating

    async def save_blueprint_rating(self, rating: ScenarioBlueprintRating) -> ScenarioBlueprintRating:
        await self._session.flush()
        await self._session.refresh(rating)
        return rating

    async def count_blueprint_ratings(self, *, blueprint_id: uuid.UUID) -> tuple[int, float]:
        result = await self._session.execute(
            select(
                func.count(ScenarioBlueprintRating.id),
                func.coalesce(func.avg(ScenarioBlueprintRating.rating), 0.0),
            ).where(ScenarioBlueprintRating.blueprint_id == blueprint_id)
        )
        row = result.one()
        return int(row[0] or 0), float(row[1] or 0.0)

    async def get_blueprint_save_by_user(
        self,
        *,
        blueprint_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ScenarioBlueprintSave | None:
        result = await self._session.execute(
            select(ScenarioBlueprintSave).where(
                ScenarioBlueprintSave.blueprint_id == blueprint_id,
                ScenarioBlueprintSave.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_blueprint_save(self, save: ScenarioBlueprintSave) -> ScenarioBlueprintSave:
        self._session.add(save)
        await self._session.flush()
        await self._session.refresh(save)
        return save

    async def delete_blueprint_save(self, save: ScenarioBlueprintSave) -> None:
        await self._session.delete(save)
        await self._session.flush()

    async def count_blueprint_saves(self, *, blueprint_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(ScenarioBlueprintSave.id)).where(ScenarioBlueprintSave.blueprint_id == blueprint_id)
        )
        return int(result.scalar_one() or 0)

    async def create_blueprint_comment(self, comment: ScenarioBlueprintComment) -> ScenarioBlueprintComment:
        self._session.add(comment)
        await self._session.flush()
        await self._session.refresh(comment)
        return comment

    async def list_blueprint_comments(
        self,
        *,
        blueprint_id: uuid.UUID,
        limit: int = 40,
    ) -> Sequence[ScenarioBlueprintComment]:
        result = await self._session.execute(
            select(ScenarioBlueprintComment)
            .where(ScenarioBlueprintComment.blueprint_id == blueprint_id)
            .order_by(ScenarioBlueprintComment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_blueprint_comments(self, *, blueprint_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(ScenarioBlueprintComment.id)).where(
                ScenarioBlueprintComment.blueprint_id == blueprint_id
            )
        )
        return int(result.scalar_one() or 0)

    async def create_workflow(self, workflow: UserScenarioWorkflow) -> UserScenarioWorkflow:
        self._session.add(workflow)
        await self._session.flush()
        await self._session.refresh(workflow)
        return workflow

    async def save_workflow(self, workflow: UserScenarioWorkflow) -> UserScenarioWorkflow:
        await self._session.flush()
        await self._session.refresh(workflow)
        return workflow

    async def get_owner_workflow(
        self,
        *,
        owner_user_id: uuid.UUID,
        workflow_id: uuid.UUID,
    ) -> UserScenarioWorkflow | None:
        result = await self._session.execute(
            select(UserScenarioWorkflow).where(
                UserScenarioWorkflow.id == workflow_id,
                UserScenarioWorkflow.owner_user_id == owner_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_owner_workflows(self, *, owner_user_id: uuid.UUID) -> Sequence[UserScenarioWorkflow]:
        result = await self._session.execute(
            select(UserScenarioWorkflow)
            .where(UserScenarioWorkflow.owner_user_id == owner_user_id)
            .order_by(UserScenarioWorkflow.updated_at.desc())
        )
        return result.scalars().all()

    async def create_workflow_run(self, run: UserScenarioWorkflowRun) -> UserScenarioWorkflowRun:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def save_workflow_run(self, run: UserScenarioWorkflowRun) -> UserScenarioWorkflowRun:
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_workflow_run_by_id(self, *, run_id: uuid.UUID) -> UserScenarioWorkflowRun | None:
        result = await self._session.execute(
            select(UserScenarioWorkflowRun).where(UserScenarioWorkflowRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_recent_workflow_runs_for_user(
        self,
        *,
        actor_user_id: uuid.UUID,
        limit: int = 12,
    ) -> Sequence[UserScenarioWorkflowRun]:
        result = await self._session.execute(
            select(UserScenarioWorkflowRun)
            .where(UserScenarioWorkflowRun.actor_user_id == actor_user_id)
            .order_by(UserScenarioWorkflowRun.last_active_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_showcase_by_share_id(self, *, share_id: str) -> ScenarioOutputShowcase | None:
        result = await self._session.execute(
            select(ScenarioOutputShowcase).where(ScenarioOutputShowcase.share_id == share_id)
        )
        return result.scalar_one_or_none()

    async def create_showcase(self, showcase: ScenarioOutputShowcase) -> ScenarioOutputShowcase:
        self._session.add(showcase)
        await self._session.flush()
        await self._session.refresh(showcase)
        return showcase

    async def save_showcase(self, showcase: ScenarioOutputShowcase) -> ScenarioOutputShowcase:
        await self._session.flush()
        await self._session.refresh(showcase)
        return showcase

    async def list_public_showcase(self, *, limit: int = 24) -> Sequence[ScenarioOutputShowcase]:
        result = await self._session.execute(
            select(ScenarioOutputShowcase)
            .where(ScenarioOutputShowcase.visibility == "public")
            .order_by(ScenarioOutputShowcase.upvotes.desc(), ScenarioOutputShowcase.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_creator_reward_event(self, *, event_key: str) -> ScenarioCreatorRewardEvent | None:
        result = await self._session.execute(
            select(ScenarioCreatorRewardEvent).where(ScenarioCreatorRewardEvent.event_key == event_key)
        )
        return result.scalar_one_or_none()

    async def create_creator_reward_event(
        self,
        event: ScenarioCreatorRewardEvent,
    ) -> ScenarioCreatorRewardEvent:
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def resolve_autonomous_owner(
        self,
        *,
        preferred_user_id: uuid.UUID | None = None,
    ) -> User | None:
        if preferred_user_id is not None:
            preferred = await self._session.execute(select(User).where(User.id == preferred_user_id))
            user = preferred.scalar_one_or_none()
            if user is not None:
                return user

        admin_result = await self._session.execute(
            select(User).where(User.role == UserRole.admin).order_by(User.created_at.asc()).limit(1)
        )
        admin = admin_result.scalar_one_or_none()
        if admin is not None:
            return admin

        user_result = await self._session.execute(select(User).order_by(User.created_at.asc()).limit(1))
        return user_result.scalar_one_or_none()

    async def create_autonomy_cycle(self, row: ScenarioAutonomyCycle) -> ScenarioAutonomyCycle:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_autonomy_cycle(self, row: ScenarioAutonomyCycle) -> ScenarioAutonomyCycle:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_autonomy_cycle_by_id(self, *, cycle_id: uuid.UUID) -> ScenarioAutonomyCycle | None:
        result = await self._session.execute(
            select(ScenarioAutonomyCycle).where(ScenarioAutonomyCycle.id == cycle_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_autonomy_cycle(self) -> ScenarioAutonomyCycle | None:
        result = await self._session.execute(
            select(ScenarioAutonomyCycle).order_by(ScenarioAutonomyCycle.started_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_recent_autonomy_cycles(self, *, limit: int = 20) -> Sequence[ScenarioAutonomyCycle]:
        result = await self._session.execute(
            select(ScenarioAutonomyCycle)
            .order_by(ScenarioAutonomyCycle.started_at.desc())
            .limit(max(1, limit))
        )
        return result.scalars().all()

    async def count_autonomy_cycles(self) -> int:
        result = await self._session.execute(select(func.count(ScenarioAutonomyCycle.id)))
        return int(result.scalar_one() or 0)

    async def create_autonomy_experiment(self, row: ScenarioAutonomyExperiment) -> ScenarioAutonomyExperiment:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_autonomy_experiment(self, row: ScenarioAutonomyExperiment) -> ScenarioAutonomyExperiment:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_autonomy_experiments(
        self,
        *,
        cycle_id: uuid.UUID,
    ) -> Sequence[ScenarioAutonomyExperiment]:
        result = await self._session.execute(
            select(ScenarioAutonomyExperiment)
            .where(ScenarioAutonomyExperiment.cycle_id == cycle_id)
            .order_by(ScenarioAutonomyExperiment.created_at.asc())
        )
        return result.scalars().all()

    async def create_autonomy_growth_decision(
        self,
        row: ScenarioAutonomyGrowthDecision,
    ) -> ScenarioAutonomyGrowthDecision:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_autonomy_growth_decisions(
        self,
        *,
        cycle_id: uuid.UUID,
    ) -> Sequence[ScenarioAutonomyGrowthDecision]:
        result = await self._session.execute(
            select(ScenarioAutonomyGrowthDecision)
            .where(ScenarioAutonomyGrowthDecision.cycle_id == cycle_id)
            .order_by(ScenarioAutonomyGrowthDecision.created_at.asc())
        )
        return result.scalars().all()

    async def create_autonomy_guardrail_event(
        self,
        row: ScenarioAutonomyGuardrailEvent,
    ) -> ScenarioAutonomyGuardrailEvent:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_autonomy_guardrail_events(
        self,
        *,
        cycle_id: uuid.UUID,
    ) -> Sequence[ScenarioAutonomyGuardrailEvent]:
        result = await self._session.execute(
            select(ScenarioAutonomyGuardrailEvent)
            .where(ScenarioAutonomyGuardrailEvent.cycle_id == cycle_id)
            .order_by(ScenarioAutonomyGuardrailEvent.created_at.asc())
        )
        return result.scalars().all()

    async def list_autonomous_blueprints(
        self,
        *,
        only_published: bool = True,
        limit: int = 240,
    ) -> Sequence[UserScenarioBlueprint]:
        stmt = select(UserScenarioBlueprint).where(UserScenarioBlueprint.autonomous_mode.is_(True))
        if only_published:
            stmt = stmt.where(UserScenarioBlueprint.is_published.is_(True))
        result = await self._session.execute(
            stmt.order_by(
                UserScenarioBlueprint.autonomous_quality_score.desc(),
                UserScenarioBlueprint.updated_at.desc(),
            ).limit(max(1, limit))
        )
        return result.scalars().all()

    async def list_autonomous_iteration_candidates(
        self,
        *,
        min_runs: int = 3,
        limit: int = 60,
    ) -> Sequence[UserScenarioBlueprint]:
        result = await self._session.execute(
            select(UserScenarioBlueprint)
            .where(
                UserScenarioBlueprint.autonomous_mode.is_(True),
                UserScenarioBlueprint.is_published.is_(True),
                UserScenarioBlueprint.run_count >= max(1, min_runs),
            )
            .order_by(
                UserScenarioBlueprint.autonomous_quality_score.asc(),
                UserScenarioBlueprint.updated_at.asc(),
            )
            .limit(max(1, limit))
        )
        return result.scalars().all()

    async def get_personalization_profile(
        self,
        *,
        user_id: uuid.UUID,
    ) -> ScenarioAutonomyPersonalizationProfile | None:
        result = await self._session.execute(
            select(ScenarioAutonomyPersonalizationProfile).where(
                ScenarioAutonomyPersonalizationProfile.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_personalization_profile(
        self,
        row: ScenarioAutonomyPersonalizationProfile,
    ) -> ScenarioAutonomyPersonalizationProfile:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_personalization_profile(
        self,
        row: ScenarioAutonomyPersonalizationProfile,
    ) -> ScenarioAutonomyPersonalizationProfile:
        await self._session.flush()
        await self._session.refresh(row)
        return row
