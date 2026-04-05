import uuid

from app.infrastructure.db.models import LessonMission, UserMissionProgress
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.experiment_service import economy_experiment_metadata
from app.modules.missions.service.mission_constants import STREAK_RECOVERY_MISSION_SLUG


class MissionAnalyticsEmitter:
    def __init__(
        self,
        *,
        analytics: AnalyticsService | None,
        wallet_repo: WalletRepository | None,
    ) -> None:
        self._analytics = analytics
        self._wallet_repo = wallet_repo

    async def emit_progress_event(
        self,
        *,
        user_id: uuid.UUID,
        mission: LessonMission,
        mission_slug: str,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        source_event_key: str,
        mission_step_id: uuid.UUID | None,
        progress: UserMissionProgress,
        cycle_number: int,
        started_now: bool,
        completed_now: bool,
    ) -> None:
        if self._analytics is None:
            return

        payer_status = "non_payer"
        if self._wallet_repo is not None:
            _, _, total_spent = await self._wallet_repo.summary(user_id)
            payer_status = "payer" if int(total_spent) > 0 else "non_payer"

        base_metadata = {
            "mission_id": str(mission.id),
            "mission_slug": mission_slug,
            "mission_action_type": mission.action_type.value,
            "source_event_key": source_event_key,
            "mission_cycle": cycle_number,
            "trigger_event_type": event_type,
            "progress_count": progress.progress_count,
            "required_count": progress.required_count,
            "prompt_id": str(prompt_id) if prompt_id is not None else None,
            "lesson_id": str(lesson_id) if lesson_id is not None else None,
            "mission_step_id": str(mission_step_id) if mission_step_id is not None else None,
            **economy_experiment_metadata(user_id=user_id, payer_status=payer_status),
        }

        if started_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_started,
                user_id=user_id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_started:{user_id}:{mission.id}:cycle:{cycle_number}",
            )

        if not completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_progressed,
                user_id=user_id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=(
                    f"mission_progressed:{user_id}:{mission.id}:cycle:{cycle_number}:"
                    f"{progress.progress_count}:{source_event_key}"
                ),
            )

        if completed_now:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.mission_completed,
                user_id=user_id,
                metadata=base_metadata,
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                event_id=f"mission_completed:{user_id}:{mission.id}:cycle:{cycle_number}",
            )
            if mission.slug == STREAK_RECOVERY_MISSION_SLUG:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.streak_recovery_completed,
                    user_id=user_id,
                    metadata=base_metadata,
                    context_page="/api/v1/missions/events",
                    context_feature="streak_recovery",
                    event_id=f"streak_recovery_completed:{user_id}:{mission.id}:cycle:{cycle_number}",
                )
