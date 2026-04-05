from __future__ import annotations

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import LessonMission, MissionActionType, User
from app.modules.missions.model.mission import MissionRead
from app.modules.missions.service.mission_constants import STREAK_RECOVERY_MISSION_SLUG


class MissionEventConfirmMixin:
    def _ensure_manual_confirmation_mission(self, mission: LessonMission, slug: str) -> None:
        if mission.action_type != MissionActionType.manual_confirmation:
            raise AppError(
                code="mission_manual_confirmation_not_allowed",
                message="Mission does not support manual confirmation",
                status_code=400,
                message_key="errors.mission_manual_confirmation_not_allowed",
            )
        if mission.slug != slug:
            raise NotFoundError("mission", slug)

    async def confirm_manual_step(self, user: User, slug: str) -> MissionRead:
        mission = await self._repo.get_mission_by_slug(slug)
        if mission is None:
            raise NotFoundError("mission", slug)

        self._ensure_manual_confirmation_mission(mission, slug)

        if mission.slug == STREAK_RECOVERY_MISSION_SLUG and self._wallet_repo is not None:
            is_available = await self._wallet_repo.should_offer_streak_recovery(user_id=user.id)
            if not is_available:
                raise AppError(
                    code="streak_recovery_unavailable",
                    message="Streak recovery is only available in the same-day recovery window.",
                    status_code=409,
                    message_key="errors.streak_recovery_unavailable",
                )

        await self.record_event(
            user=user,
            event_type="mission_manual_confirmed",
            source_event_key=f"mission_manual_confirmed:{user.id}:{mission.id}",
        )
        if mission.slug == STREAK_RECOVERY_MISSION_SLUG and self._wallet_repo is not None:
            await self._wallet_repo.record_daily_check_in(user.id)
        return await self.get_mission_by_slug(user, slug)
