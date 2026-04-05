from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.db.models import User
from app.modules.missions.service.mission_types import MissionEventContext


class MissionEventContextMixin:
    async def _build_mission_event_context(self, *, user: User) -> MissionEventContext:
        now = datetime.now(timezone.utc)
        profile = await self._onboarding.get_profile(user.id)
        segment = (
            await self._wallet_repo.classify_user_segment(user_id=user.id, now=now)
            if self._wallet_repo is not None
            else "balanced"
        )
        missions = await self._repo.list_active_missions()
        mission_by_slug = {mission.slug: mission for mission in missions}
        eligible_missions = [
            mission
            for mission in missions
            if self._policy.is_eligible(mission, profile, segment=segment)
        ]
        mission_slug_by_id = {mission.id: mission.slug for mission in eligible_missions}

        progress_rows = await self._repo.list_user_progress(user.id)
        progress_map = {row.mission_id: row for row in progress_rows}
        step_progress_rows = await self._repo.list_user_step_progress(user.id)
        step_progress_map = {row.mission_step_id: row for row in step_progress_rows}
        return MissionEventContext(
            now=now,
            segment=segment,
            mission_by_slug=mission_by_slug,
            eligible_missions=eligible_missions,
            mission_slug_by_id=mission_slug_by_id,
            progress_map=progress_map,
            step_progress_map=step_progress_map,
        )
