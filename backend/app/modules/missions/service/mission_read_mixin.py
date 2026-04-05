from __future__ import annotations

from app.modules.missions.service.mission_read_listing_mixin import MissionReadListingMixin
from app.modules.missions.service.mission_read_next_step_mixin import MissionReadNextStepMixin
from app.modules.missions.service.mission_read_projection_mixin import MissionReadProjectionMixin


class MissionReadMixin(
    MissionReadListingMixin,
    MissionReadProjectionMixin,
    MissionReadNextStepMixin,
):
    """Composed mission read mixin with separated concerns."""

