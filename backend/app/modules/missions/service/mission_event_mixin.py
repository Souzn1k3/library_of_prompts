from __future__ import annotations

from app.modules.missions.service.mission_event_progress_mixin import MissionEventProgressMixin
from app.modules.missions.service.mission_event_runtime_mixin import MissionEventRuntimeMixin


class MissionEventMixin(
    MissionEventRuntimeMixin,
    MissionEventProgressMixin,
):
    """Composed mission event mixin with separated concerns."""

