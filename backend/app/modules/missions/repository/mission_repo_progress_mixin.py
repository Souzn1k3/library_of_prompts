from app.infrastructure.db.models import (
    MissionProgressStatus,
    UserMissionProgress,
    UserMissionStepProgress,
)


class MissionRepositoryProgressMixin:
    async def create_progress(self, progress: UserMissionProgress) -> UserMissionProgress:
        self._session.add(progress)
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def create_step_progress(self, progress: UserMissionStepProgress) -> UserMissionStepProgress:
        self._session.add(progress)
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def save_progress(self, progress: UserMissionProgress) -> UserMissionProgress:
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def save_step_progress(self, progress: UserMissionStepProgress) -> UserMissionStepProgress:
        await self._session.flush()
        await self._session.refresh(progress)
        return progress

    async def reset_progress_cycle(
        self,
        *,
        progress: UserMissionProgress,
        step_progress_rows: list[UserMissionStepProgress],
    ) -> None:
        progress.status = MissionProgressStatus.not_started
        progress.progress_count = 0
        progress.started_at = None
        progress.last_event_at = None
        progress.completed_at = None
        progress.reward_granted_at = None

        for row in step_progress_rows:
            row.status = MissionProgressStatus.not_started
            row.progress_count = 0
            row.started_at = None
            row.last_event_at = None
            row.completed_at = None

        await self._session.flush()
