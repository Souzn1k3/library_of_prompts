from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    LearningAchievement,
    LearningCourseProgress,
    LearningLessonProgress,
    LearningRewardGrant,
    LearningStepProgress,
    Lesson,
    PlanTier,
)


class LearningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    async def get_course_progress(self, user_id: uuid.UUID, course_slug: str) -> LearningCourseProgress | None:
        row = await self._session.execute(
            select(LearningCourseProgress).where(
                LearningCourseProgress.user_id == user_id,
                LearningCourseProgress.course_slug == course_slug,
            )
        )
        return row.scalar_one_or_none()

    async def list_course_progress(self, user_id: uuid.UUID) -> list[LearningCourseProgress]:
        rows = await self._session.execute(
            select(LearningCourseProgress)
            .where(LearningCourseProgress.user_id == user_id)
            .order_by(LearningCourseProgress.last_activity_at.desc().nullslast())
        )
        return list(rows.scalars().all())

    async def save_course_progress(self, row: LearningCourseProgress) -> LearningCourseProgress:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def create_course_progress(self, row: LearningCourseProgress) -> LearningCourseProgress:
        self._session.add(row)
        return await self.save_course_progress(row)

    async def get_lesson_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        lesson_slug: str,
    ) -> LearningLessonProgress | None:
        row = await self._session.execute(
            select(LearningLessonProgress).where(
                LearningLessonProgress.user_id == user_id,
                LearningLessonProgress.course_slug == course_slug,
                LearningLessonProgress.lesson_slug == lesson_slug,
            )
        )
        return row.scalar_one_or_none()

    async def list_lesson_progress(self, *, user_id: uuid.UUID, course_slug: str) -> list[LearningLessonProgress]:
        rows = await self._session.execute(
            select(LearningLessonProgress).where(
                LearningLessonProgress.user_id == user_id,
                LearningLessonProgress.course_slug == course_slug,
            )
        )
        return list(rows.scalars().all())

    async def save_lesson_progress(self, row: LearningLessonProgress) -> LearningLessonProgress:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def create_lesson_progress(self, row: LearningLessonProgress) -> LearningLessonProgress:
        self._session.add(row)
        return await self.save_lesson_progress(row)

    async def get_step_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        lesson_slug: str,
        step_slug: str,
    ) -> LearningStepProgress | None:
        row = await self._session.execute(
            select(LearningStepProgress).where(
                LearningStepProgress.user_id == user_id,
                LearningStepProgress.course_slug == course_slug,
                LearningStepProgress.lesson_slug == lesson_slug,
                LearningStepProgress.step_slug == step_slug,
            )
        )
        return row.scalar_one_or_none()

    async def list_step_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        lesson_slug: str | None = None,
    ) -> list[LearningStepProgress]:
        where = [
            LearningStepProgress.user_id == user_id,
            LearningStepProgress.course_slug == course_slug,
        ]
        if lesson_slug is not None:
            where.append(LearningStepProgress.lesson_slug == lesson_slug)
        rows = await self._session.execute(select(LearningStepProgress).where(*where))
        return list(rows.scalars().all())

    async def save_step_progress(self, row: LearningStepProgress) -> LearningStepProgress:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def create_step_progress(self, row: LearningStepProgress) -> LearningStepProgress:
        self._session.add(row)
        return await self.save_step_progress(row)

    async def grant_reward(
        self,
        *,
        user_id: uuid.UUID,
        grant_key: str,
        reward_type: str,
        course_slug: str | None,
        lesson_slug: str | None,
        lmn_amount: int,
        meta: dict[str, Any] | None = None,
    ) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            self._insert(LearningRewardGrant)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                grant_key=grant_key,
                reward_type=reward_type,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
                lmn_amount=lmn_amount,
                meta=meta,
                created_at=now,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "grant_key"])
        )

        if not self._is_sqlite():
            stmt = stmt.returning(LearningRewardGrant.id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None

        result = await self._session.execute(stmt)
        return int(result.rowcount or 0) > 0

    async def grant_achievement(
        self,
        *,
        user_id: uuid.UUID,
        achievement_code: str,
        course_slug: str | None,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            self._insert(LearningAchievement)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                achievement_code=achievement_code,
                course_slug=course_slug,
                payload=payload,
                issued_at=now,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "achievement_code"])
        )

        if not self._is_sqlite():
            stmt = stmt.returning(LearningAchievement.id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None

        result = await self._session.execute(stmt)
        return int(result.rowcount or 0) > 0

    async def list_achievements(self, user_id: uuid.UUID) -> list[LearningAchievement]:
        rows = await self._session.execute(
            select(LearningAchievement)
            .where(LearningAchievement.user_id == user_id)
            .order_by(LearningAchievement.issued_at.desc())
        )
        return list(rows.scalars().all())

    async def get_legacy_lesson_by_slug(self, slug: str) -> Lesson | None:
        row = await self._session.execute(select(Lesson).where(Lesson.slug == slug))
        return row.scalar_one_or_none()

    async def ensure_legacy_lesson(
        self,
        *,
        slug: str,
        title: str,
        body: str,
        sort_order: int,
    ) -> Lesson:
        existing = await self.get_legacy_lesson_by_slug(slug)
        if existing is not None:
            changed = False
            if existing.title != title:
                existing.title = title
                changed = True
            if existing.body != body:
                existing.body = body
                changed = True
            if existing.sort_order != sort_order:
                existing.sort_order = sort_order
                changed = True
            if changed:
                await self._session.flush()
            return existing

        row = Lesson(
            slug=slug,
            title=title,
            body=body,
            min_tier=PlanTier.free,
            sort_order=sort_order,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

