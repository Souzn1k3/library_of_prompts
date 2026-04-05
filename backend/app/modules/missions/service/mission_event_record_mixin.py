from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.db.models import User


class MissionEventRecordMixin:
    async def record_event(
        self,
        *,
        user: User,
        event_type: str,
        prompt_id: uuid.UUID | None = None,
        lesson_id: uuid.UUID | None = None,
        source_event_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[str]:
        context = await self._build_mission_event_context(user=user)
        completed_slugs: list[str] = []

        for mission in context.eligible_missions:
            await self._reset_progress_cycle_if_needed(
                mission,
                context.progress_map.get(mission.id),
                step_progress=context.step_progress_map,
                now=context.now,
            )
            if not self._policy.is_chain_unlocked(
                mission,
                mission_by_slug=context.mission_by_slug,
                progress_map=context.progress_map,
            ):
                continue
            target_steps = self._event_matcher.matching_target_steps(
                mission,
                event_type=event_type,
                prompt_id=prompt_id,
                lesson_id=lesson_id,
            )
            if not target_steps:
                continue

            progress = await self._ensure_progress(
                user_id=user.id,
                mission=mission,
                progress_map=context.progress_map,
            )
            if progress.completed_at is not None:
                continue

            current_cycle = max(1, progress.completion_count + 1)

            for step in target_steps:
                step_progress = await self._ensure_step_progress(
                    user_id=user.id,
                    step=step,
                    step_progress_map=context.step_progress_map,
                )
                if step is not None and (step_progress is None or step_progress.completed_at is not None):
                    continue
                if await self._is_event_on_cooldown(
                    user_id=user.id,
                    mission_id=mission.id,
                    event_type=event_type,
                    now=context.now,
                ):
                    continue

                completed_now = await self._apply_event_to_progress(
                    user=user,
                    mission=mission,
                    mission_slug=context.mission_slug_by_id.get(mission.id, mission.slug),
                    step=step,
                    progress=progress,
                    step_progress_map=context.step_progress_map,
                    current_cycle=current_cycle,
                    event_type=event_type,
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                    source_event_key=source_event_key,
                    payload=payload,
                    segment=context.segment,
                    now=context.now,
                )
                if completed_now:
                    completed_slugs.append(mission.slug)

        return completed_slugs
