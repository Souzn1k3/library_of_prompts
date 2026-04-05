from app.modules.economy.repository.insights_repository import EconomyInsightsRepository
from app.modules.economy.service.insights_experiment_mixin import EconomyInsightsExperimentMixin
from app.modules.economy.service.insights_support_mixin import EconomyInsightsSupportMixin
from app.modules.economy.service.insights_tuning_mixin import EconomyInsightsTuningMixin


class EconomyInsightsService(
    EconomyInsightsSupportMixin,
    EconomyInsightsExperimentMixin,
    EconomyInsightsTuningMixin,
):
    def __init__(self, repo: EconomyInsightsRepository) -> None:
        self._repo = repo
