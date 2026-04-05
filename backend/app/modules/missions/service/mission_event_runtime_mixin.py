from __future__ import annotations

from app.modules.missions.service.mission_event_apply_mixin import MissionEventApplyMixin
from app.modules.missions.service.mission_event_confirm_mixin import MissionEventConfirmMixin
from app.modules.missions.service.mission_event_context_mixin import MissionEventContextMixin
from app.modules.missions.service.mission_event_record_mixin import MissionEventRecordMixin


class MissionEventRuntimeMixin(
    MissionEventConfirmMixin,
    MissionEventRecordMixin,
    MissionEventApplyMixin,
    MissionEventContextMixin,
):
    """Runtime mission-event flow composed from narrow mixins."""

