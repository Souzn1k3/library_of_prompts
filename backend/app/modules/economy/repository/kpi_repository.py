from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.economy.repository.kpi_base_mixin import EconomyKpiBaseMixin
from app.modules.economy.repository.kpi_daily_mixin import EconomyKpiDailyMixin
from app.modules.economy.repository.kpi_event_query_mixin import EconomyKpiEventQueryMixin


class EconomyKpiRepository(EconomyKpiDailyMixin, EconomyKpiEventQueryMixin, EconomyKpiBaseMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
