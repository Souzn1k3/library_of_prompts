from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.infrastructure.db.models import LessonMission, MissionProgressStatus, MissionStep, User, UserMissionProgress, UserMissionStepProgress


class MissionEventApplyMixin:
    async def _apply_event_to_progress(
        self,
        *,
        user: User,
        mission: LessonMission,
        mission_slug: str,
        step: MissionStep | None,
        progress: UserMissionProgress,
        step_progress_map: dict[uuid.UUID, UserMissionStepProgress],
        current_cycle: int,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        source_event_key: str | None,
        payload: dict[str, Any] | None,
        segment: str,
        now: datetime,
    ) -> bool | None:
        scoped_key = source_event_key or f"{event_type}:{uuid.uuid4()}"
        completion_event = await self._repo.add_completion_event(
            progress_id=progress.id,
            user_id=user.id,
            mission_id=mission.id,
            mission_step_id=step.id if step is not None else None,
            event_type=event_type,
            source_event_key=f"{mission.id}:cycle:{current_cycle}:{scoped_key}",
            prompt_id=prompt_id,
            lesson_id=lesson_id,
            payload=payload,
            created_at=now,
        )
        if completion_event is None:
            return None

        started_now = progress.started_at is None
        if started_now:
            progress.started_at = now
        progress.last_event_at = now
        progress.status = MissionProgressStatus.in_progress

        if step is not None:
            step_progress = step_progress_map.get(step.id)
            if step_progress is None:
                return None
            await self._apply_step_progress(
                user=user,
                mission=mission,
                step=step,
                step_progress=step_progress,
                cycle_number=current_cycle,
                event_type=event_type,
                source_key=scoped_key,
                segment=segment,
                now=now,
            )
        else:
            progress.progress_count = min(progress.required_count, progress.progress_count + 1)

        if mission.steps:
            progress.required_count, progress.progress_count = self._policy.step_progress_totals(
                mission,
                step_progress_map,
            )

        completed_now = await self._finalize_progress_completion(
            user=user,
            mission=mission,
            progress=progress,
            cycle_number=current_cycle,
            segment=segment,
            now=now,
        )
        await self._repo.save_progress(progress)
        await self._analytics_emitter.emit_progress_event(
            user_id=user.id,
            mission=mission,
            mission_slug=mission_slug,
            event_type=event_type,
            prompt_id=prompt_id,
            lesson_id=lesson_id,
            source_event_key=scoped_key,
            mission_step_id=step.id if step is not None else None,
            progress=progress,
            cycle_number=current_cycle,
            started_now=started_now,
            completed_now=completed_now,
        )
        return completed_now
