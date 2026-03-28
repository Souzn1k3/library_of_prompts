from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.infrastructure.db.models import CurrencyTransactionType, PurchaseStatus, StoreItemKind


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


class WalletRead(BaseModel):
    balance: int
    currency: str = "LMN"
    currency_name: str = "Lumens"
    currency_symbol: str = "LMN"
    total_earned: int
    total_spent: int
    current_streak: int = 0
    best_streak: int = 0
    last_check_in_at: datetime | None = None
    check_in_available: bool = True
    premium_unlock_until: datetime | None = None
    active_benefits: list[WalletBenefitRead] = []
    recent_purchases: list[WalletPurchaseRead] = []
    recent: list[CurrencyTransactionRead]
