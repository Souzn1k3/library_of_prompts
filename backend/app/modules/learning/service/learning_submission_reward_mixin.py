from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.infrastructure.db.models import CurrencyTransactionType, LearningLessonProgress, User
from app.modules.learning.service.learning_types import MissionServiceProtocol, RewardState, StoreServiceProtocol


class LearningSubmissionRewardMixin:
    async def _record_learning_lesson_missions(
        self,
        *,
        user: User,
        course_slug: str,
        lesson_slug: str,
        missions: MissionServiceProtocol,
    ) -> list[str]:
        completed_mission_slugs: list[str] = []
        legacy_lesson = await self._repo.get_legacy_lesson_by_slug(lesson_slug)
        if legacy_lesson is not None:
            completed_mission_slugs.extend(
                await missions.record_event(
                    user=user,
                    event_type="lesson_completed",
                    lesson_id=legacy_lesson.id,
                    source_event_key=f"learning_lesson_completed:{user.id}:{course_slug}:{lesson_slug}",
                )
            )
        completed_mission_slugs.extend(
            await missions.record_event(
                user=user,
                event_type="streak_activity",
                source_event_key=f"learning_streak:{user.id}:{datetime.now(timezone.utc).date().isoformat()}",
                payload={"source": "learning_lesson_completed", "course_slug": course_slug},
            )
        )
        return completed_mission_slugs

    async def _apply_lesson_completion_reward(
        self,
        *,
        user: User,
        course_slug: str,
        lesson_slug: str,
        step_slug: str,
        lesson: dict,
        course: dict,
        lesson_progress: LearningLessonProgress,
        missions: MissionServiceProtocol,
        store: StoreServiceProtocol,
        reward_state: RewardState,
    ) -> None:
        lesson_reward = int(lesson.get("reward_lmn", course.get("lesson_default_reward_lmn", 0)))
        reward_key = f"lesson:{course_slug}:{lesson_slug}"
        granted = await self._repo.grant_reward(
            user_id=user.id,
            grant_key=reward_key,
            reward_type="lesson_completion",
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            lmn_amount=lesson_reward,
            meta={"step_slug": step_slug},
        )
        if not granted:
            return

        previous_balance, _, _ = await self._wallet.summary(user.id)
        await self._wallet.adjust_balance(
            user_id=user.id,
            amount=lesson_reward,
            reason=CurrencyTransactionType.mission_reward,
            context=f"learning:lesson:{course_slug}:{lesson_slug}",
            source_id=uuid.uuid5(uuid.NAMESPACE_URL, reward_key),
            metadata={"course_slug": course_slug, "lesson_slug": lesson_slug},
        )
        reward_state.awarded_lmn += lesson_reward
        lesson_progress.lmn_reward_granted = True
        await self._repo.save_lesson_progress(lesson_progress)

        reward_state.completed_mission_slugs.extend(
            await self._record_learning_lesson_missions(
                user=user,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
                missions=missions,
            )
        )
        reward_state.economy = await store.build_action_feedback(
            user,
            previous_balance=previous_balance,
            completed_mission_slugs=list(dict.fromkeys(reward_state.completed_mission_slugs)),
        )

    async def _apply_course_completion_reward(
        self,
        *,
        user: User,
        course_slug: str,
        course: dict,
        store: StoreServiceProtocol,
        reward_state: RewardState,
    ) -> None:
        course_reward = int(course.get("course_reward_lmn", 0))
        reward_key = f"course:{course_slug}"
        granted = await self._repo.grant_reward(
            user_id=user.id,
            grant_key=reward_key,
            reward_type="course_completion",
            course_slug=course_slug,
            lesson_slug=None,
            lmn_amount=course_reward,
            meta={"completed_at": datetime.now(timezone.utc).isoformat()},
        )
        if not granted:
            return

        previous_balance, _, _ = await self._wallet.summary(user.id)
        await self._wallet.adjust_balance(
            user_id=user.id,
            amount=course_reward,
            reason=CurrencyTransactionType.mission_reward,
            context=f"learning:course:{course_slug}",
            source_id=uuid.uuid5(uuid.NAMESPACE_URL, reward_key),
            metadata={"course_slug": course_slug, "reward_type": "course_completion"},
        )
        reward_state.awarded_lmn += course_reward
        reward_state.awarded_badge = str(course.get("badge_code"))
        await self._repo.grant_achievement(
            user_id=user.id,
            achievement_code=f"course:{course_slug}:{reward_state.awarded_badge}",
            course_slug=course_slug,
            payload={
                "badge_code": reward_state.awarded_badge,
                "certificate_template": course.get("certificate_template"),
            },
        )
        reward_state.certificate_ready = True
        reward_state.economy = await store.build_action_feedback(
            user,
            previous_balance=previous_balance,
            completed_mission_slugs=list(dict.fromkeys(reward_state.completed_mission_slugs)),
        )
