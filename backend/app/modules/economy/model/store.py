from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.infrastructure.db.models import PurchaseStatus, StoreItemKind
from app.modules.economy.model.wallet import WalletRead


class StoreItemRead(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    price: int
    kind: StoreItemKind
    availability: int | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool
    owned: bool = False
    is_affordable: bool = False
    remaining_lumens: int = 0
    progress_ratio: float = 0
    price_band: str = "entry"
    tags: list[str] = Field(default_factory=list)
    starter_type: str | None = None
    is_limited_offer: bool = False
    offer_ends_at: datetime | None = None
    offer_reason: str | None = None
    dynamic_offer: bool = False
    upgrade_tier: int = 1
    max_tier: int = 1
    next_upgrade_cost: int | None = None
    boost_pct: int | None = None
    boost_missions_left: int | None = None
    near_miss_delta: int = 0


class StorePurchaseRequest(BaseModel):
    client_token: str | None = Field(default=None, min_length=8, max_length=80)


class PurchaseRead(BaseModel):
    id: uuid.UUID
    status: PurchaseStatus
    price_paid: int
    metadata: dict[str, Any] | None = None
    client_token: str | None = None
    item: StoreItemRead
    created_at: datetime


class StoreRewardRead(BaseModel):
    kind: str
    title: str
    description: str | None = None
    amount: int | None = None
    metadata: dict[str, Any] | None = None


class EconomyActionRead(BaseModel):
    wallet: WalletRead | None = None
    balance: int | None = None
    available_items: list[StoreItemRead] = Field(default_factory=list)
    newly_affordable_items: list[StoreItemRead] = Field(default_factory=list)
    best_item: StoreItemRead | None = None
    balance_delta: int = 0
    completed_mission_slugs: list[str] = Field(default_factory=list)
    near_miss_message: str | None = None


class PurchaseResult(BaseModel):
    purchase: PurchaseRead
    wallet: WalletRead
    available_items: list[StoreItemRead] = Field(default_factory=list)
    newly_affordable_items: list[StoreItemRead] = Field(default_factory=list)
    best_item: StoreItemRead | None = None
    first_purchase_reward: StoreRewardRead | None = None
    locked_cashback_reward: StoreRewardRead | None = None
    second_purchase_challenge_reward: StoreRewardRead | None = None
