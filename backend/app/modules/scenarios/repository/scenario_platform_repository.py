from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    ScenarioCreatorRewardEvent,
    ScenarioOutputShowcase,
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
