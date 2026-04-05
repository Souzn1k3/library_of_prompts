from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.missions.repository.mission_repo_base_mixin import MissionRepositoryBaseMixin
from app.modules.missions.repository.mission_repo_event_mixin import MissionRepositoryEventMixin
from app.modules.missions.repository.mission_repo_progress_mixin import MissionRepositoryProgressMixin
from app.modules.missions.repository.mission_repo_read_mixin import MissionRepositoryReadMixin
from app.modules.missions.repository.mission_repo_reward_mixin import MissionRepositoryRewardMixin


class MissionRepository(
    MissionRepositoryBaseMixin,
    MissionRepositoryReadMixin,
    MissionRepositoryProgressMixin,
    MissionRepositoryEventMixin,
    MissionRepositoryRewardMixin,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
