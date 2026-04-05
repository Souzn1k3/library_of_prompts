from app.modules.economy.repository.kpi_repository import EconomyKpiRepository
from app.modules.economy.service.kpi_aggregation_mixin import EconomyKpiAggregationMixin
from app.modules.economy.service.kpi_reporting_mixin import EconomyKpiReportingMixin
from app.modules.economy.service.kpi_stats_mixin import EconomyKpiStatsMixin


class EconomyKpiService(EconomyKpiReportingMixin, EconomyKpiAggregationMixin, EconomyKpiStatsMixin):
    def __init__(self, repo: EconomyKpiRepository) -> None:
        self._repo = repo
