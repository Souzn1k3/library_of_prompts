import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.infrastructure.db.models import (
    ContributorProfile,
    ModerationState,
    MissionCompletionEvent,
    Prompt,
    PromptQualityMetric,
    PromptStats,
)


class ContributorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _insert(self, model):
        bind = self._session.bind
        if bind and bind.dialect.name == "sqlite":
            return sqlite_insert(model)
        return pg_insert(model)

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> ContributorProfile | None:
        stmt = (
            select(ContributorProfile)
            .where(ContributorProfile.user_id == user_id)
            .options(joinedload(ContributorProfile.user))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_profile_by_slug(self, slug: str) -> ContributorProfile | None:
        stmt = (
            select(ContributorProfile)
            .where(ContributorProfile.slug == slug)
            .options(joinedload(ContributorProfile.user))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_top_profiles(self, *, limit: int) -> list[ContributorProfile]:
        stmt = (
            select(ContributorProfile)
            .where(ContributorProfile.total_submissions > 0)
            .options(joinedload(ContributorProfile.user))
            .order_by(
                ContributorProfile.reputation_score.desc(),
                ContributorProfile.approved_submissions.desc(),
                ContributorProfile.total_saves.desc(),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_profile(self, profile: ContributorProfile) -> ContributorProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def save_profile(self, profile: ContributorProfile) -> ContributorProfile:
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(func.count()).where(ContributorProfile.slug == slug))
        return int(result.scalar_one() or 0) > 0

    async def count_recent_submissions(self, user_id: uuid.UUID, *, hours: int = 24) -> int:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(func.count()).select_from(Prompt).where(Prompt.author_id == user_id, Prompt.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def count_pending_submissions(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Prompt)
            .where(
                Prompt.author_id == user_id,
                Prompt.moderation_state == ModerationState.pending,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def has_recent_duplicate_submission(
        self,
        user_id: uuid.UUID,
        *,
        title: str,
        body: str,
        hours: int = 24,
    ) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(func.count()).select_from(Prompt).where(
            Prompt.author_id == user_id,
            Prompt.created_at >= since,
            func.lower(Prompt.title) == title.strip().lower(),
            Prompt.body == body,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0) > 0

    async def calculate_user_signal_snapshot(self, user_id: uuid.UUID) -> dict[str, Any]:
        stats_stmt = (
            select(
                func.count(Prompt.id).label("total_submissions"),
                func.sum(case((Prompt.moderation_state == ModerationState.approved, 1), else_=0)).label(
                    "approved_submissions"
                ),
                func.sum(case((Prompt.moderation_state == ModerationState.rejected, 1), else_=0)).label(
                    "rejected_submissions"
                ),
                func.sum(
                    case(
                        (Prompt.moderation_state == ModerationState.approved, func.coalesce(PromptStats.save_count, 0)),
                        else_=0,
                    )
                ).label("total_saves"),
                func.sum(
                    case(
                        (Prompt.moderation_state == ModerationState.approved, func.coalesce(PromptStats.copy_count, 0)),
                        else_=0,
                    )
                ).label("total_copies"),
                func.avg(
                    case(
                        (
                            Prompt.moderation_state == ModerationState.approved,
                            func.coalesce(PromptQualityMetric.quality_score, 0),
                        ),
                        else_=None,
                    )
                ).label("average_prompt_quality"),
            )
            .select_from(Prompt)
            .outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id)
            .outerjoin(PromptQualityMetric, PromptQualityMetric.prompt_id == Prompt.id)
            .where(Prompt.author_id == user_id)
        )
        stats_row = (await self._session.execute(stats_stmt)).one()

        mission_stmt = (
            select(func.count(MissionCompletionEvent.id))
            .select_from(MissionCompletionEvent)
            .join(Prompt, Prompt.id == MissionCompletionEvent.prompt_id)
            .where(Prompt.author_id == user_id)
        )
        mission_success_count = int((await self._session.execute(mission_stmt)).scalar_one() or 0)

        approved = int(stats_row.approved_submissions or 0)
        rejected = int(stats_row.rejected_submissions or 0)
        reviewed = approved + rejected
        rejection_rate = int(round((rejected / reviewed) * 100)) if reviewed > 0 else 0

        return {
            "total_submissions": int(stats_row.total_submissions or 0),
            "approved_submissions": approved,
            "rejected_submissions": rejected,
            "rejection_rate": rejection_rate,
            "total_saves": int(stats_row.total_saves or 0),
            "total_copies": int(stats_row.total_copies or 0),
            "mission_success_count": mission_success_count,
            "average_prompt_quality": int(round(float(stats_row.average_prompt_quality or 0))),
        }

    async def get_prompt_author_id(self, prompt_id: uuid.UUID) -> uuid.UUID | None:
        result = await self._session.execute(select(Prompt.author_id).where(Prompt.id == prompt_id))
        author_id = result.scalar_one_or_none()
        return author_id

    async def calculate_prompt_quality_snapshot(self, prompt_id: uuid.UUID) -> dict[str, int] | None:
        stats_stmt = (
            select(
                func.coalesce(PromptStats.save_count, 0).label("unique_savers"),
                func.coalesce(PromptStats.copy_count, 0).label("copy_events"),
                func.coalesce(func.count(MissionCompletionEvent.id), 0).label("mission_success_events"),
            )
            .select_from(Prompt)
            .outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id)
            .outerjoin(
                MissionCompletionEvent,
                MissionCompletionEvent.prompt_id == Prompt.id,
            )
            .where(Prompt.id == prompt_id)
            .group_by(PromptStats.save_count, PromptStats.copy_count)
        )
        row = (await self._session.execute(stats_stmt)).one_or_none()
        if row is None:
            return None

        unique_savers = int(row.unique_savers or 0)
        copy_events = int(row.copy_events or 0)
        mission_success_events = int(row.mission_success_events or 0)
        quality_score = min(100, max(0, (unique_savers * 4) + (copy_events * 2) + (mission_success_events * 5)))
        return {
            "unique_savers": unique_savers,
            "copy_events": copy_events,
            "mission_success_events": mission_success_events,
            "quality_score": int(quality_score),
        }

    async def upsert_prompt_quality_metric(self, prompt_id: uuid.UUID, data: dict[str, int]) -> None:
        stmt = (
            self._insert(PromptQualityMetric)
            .values(
                prompt_id=prompt_id,
                unique_savers=data["unique_savers"],
                copy_events=data["copy_events"],
                mission_success_events=data["mission_success_events"],
                quality_score=data["quality_score"],
                computed_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_update(
                index_elements=["prompt_id"],
                set_={
                    "unique_savers": data["unique_savers"],
                    "copy_events": data["copy_events"],
                    "mission_success_events": data["mission_success_events"],
                    "quality_score": data["quality_score"],
                    "computed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        )
        await self._session.execute(stmt)
