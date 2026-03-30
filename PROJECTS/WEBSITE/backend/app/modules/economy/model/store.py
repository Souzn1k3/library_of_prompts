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


class PurchaseResult(BaseModel):
    purchase: PurchaseRead
    wallet: WalletRead
