from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LockedRewardStatus,
    PurchaseStatus,
    StoreItemKind,
)


class CurrencyTransactionRead(BaseModel):
    id: uuid.UUID
    amount: int
    balance_after: int
    reason: CurrencyTransactionType
    context: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class WalletBenefitRead(BaseModel):
    key: str
    kind: str
    metadata: dict[str, Any] | None = None
    expires_at: datetime | None = None


class WalletPurchaseRead(BaseModel):
    id: uuid.UUID
    item_slug: str
    item_title: str
    kind: StoreItemKind
    price_paid: int
    status: PurchaseStatus
    metadata: dict[str, Any] | None = None
    created_at: datetime


class WalletLockedRewardRead(BaseModel):
    id: uuid.UUID
    amount: int
    status: LockedRewardStatus
    required_mission_count: int
    completed_mission_count: int
    unlock_by: datetime | None = None
    created_at: datetime
    metadata: dict[str, Any] | None = None


class WalletGoalRead(BaseModel):
    layer: str
    key: str
    title: str
    description: str
    progress: int
    target: int
    reward: str | None = None
    expires_at: datetime | None = None


class WalletStreakMilestoneRead(BaseModel):
    streak: int
    reward: int


class WalletEconomyConfigRead(BaseModel):
    daily_ladder_rewards: list[int]
    streak_milestones: list[WalletStreakMilestoneRead] = Field(default_factory=list)
    near_miss_max_delta: int


class WalletRead(BaseModel):
    balance: int
    currency: str = "LMN"
    currency_name: str = "Lumens"
    currency_symbol: str = "LMN"
    total_earned: int
    total_spent: int
    current_streak: int = 0
    best_streak: int = 0
    spend_streak_days: int = 0
    spend_streak_mult: float = 1.0
    streak_freeze_tokens: int = 0
    last_check_in_at: datetime | None = None
    check_in_available: bool = True
    pending_locked_rewards: list[WalletLockedRewardRead] = Field(default_factory=list)
    rank_points: int = 0
    rank_level: int = 1
    rank_next_threshold: int = 0
    owned_value_generated: int = 0
    goals: list[WalletGoalRead] = Field(default_factory=list)
    economy_config: WalletEconomyConfigRead | None = None
    premium_unlock_until: datetime | None = None
    active_benefits: list[WalletBenefitRead] = Field(default_factory=list)
    recent_purchases: list[WalletPurchaseRead] = Field(default_factory=list)
    recent: list[CurrencyTransactionRead]
