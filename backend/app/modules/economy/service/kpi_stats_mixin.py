from __future__ import annotations

import statistics


class EconomyKpiStatsMixin:
    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(float(numerator) / float(denominator), 4)

    def _mean(self, values: list[float], *, digits: int = 2) -> float | None:
        if not values:
            return None
        return round(float(statistics.fmean(values)), digits)

    def _median(self, values: list[float], *, digits: int = 2) -> float | None:
        if not values:
            return None
        return round(float(statistics.median(values)), digits)
