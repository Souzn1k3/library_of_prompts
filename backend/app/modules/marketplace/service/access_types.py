from dataclasses import dataclass


@dataclass(slots=True)
class PlanAccessContext:
    total_unlocks: int = 0
    remaining_unlocks: int = 0
    money_discount_percent: int = 0
    lumen_discount_percent: int = 0
