import enum
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import (
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    PurchaseStatus,
    PromptPaymentMethod,
    ReviewModerationStatus,
)


class ReviewSort(str, enum.Enum):
    new = "new"
    best = "best"


class CatalogAction(str, enum.Enum):
    open = "open"
    buy = "buy"
    signin = "signin"


class PromptPriceRead(BaseModel):
    price_rub: int
    price_lumens: int
    commission_percent: int = 5


class PromptAccessRead(BaseModel):
    has_access: bool
    is_owned: bool = False
    source: str | None = None
    can_unlock_with_plan: bool = False
    remaining_plan_unlocks: int = 0
    monthly_plan_unlocks: int = 0
    purchase_required: bool = False
    catalog_action: CatalogAction = CatalogAction.open


class PromptReviewWrite(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=3000)


class PromptReviewRead(BaseModel):
    id: uuid.UUID
    rating: int
    text: str | None = None
    author_user_id: uuid.UUID
    author_display_name: str
    author_slug: str | None = None
    prompt_id: uuid.UUID
    prompt_slug: str
    prompt_title: str
    created_at: datetime
    updated_at: datetime
    verified_purchase: bool = True
    moderation_status: ReviewModerationStatus = ReviewModerationStatus.visible
    moderation_reason: str | None = None
    reported_count: int = 0


class PromptReviewListRead(BaseModel):
    seller_user_id: uuid.UUID | None = None
    rating_average: float | None = None
    rating_display: float | None = None
    review_count: int = 0
    sort: ReviewSort
    items: list[PromptReviewRead] = []


class PromptPurchaseRead(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    prompt_slug: str
    prompt_title: str
    seller_user_id: uuid.UUID | None = None
    status: PurchaseStatus
    payment_method: PromptPaymentMethod
    price_rub: int
    price_lumens: int
    settlement_status: MarketplaceSettlementStatus = MarketplaceSettlementStatus.pending
    settlement_available_at: datetime | None = None
    paid_out_at: datetime | None = None
    created_at: datetime
    completed_at: datetime | None = None
    can_review: bool = False
    review: PromptReviewRead | None = None


class PromptPurchaseListRead(BaseModel):
    items: list[PromptPurchaseRead] = []
    total: int = 0


class PromptPurchaseActionResponse(BaseModel):
    purchase: PromptPurchaseRead
    access: PromptAccessRead


class PromptCheckoutSessionRequest(BaseModel):
    prompt_id: uuid.UUID
    client_token: str | None = Field(default=None, min_length=8, max_length=80)
    success_url: str | None = Field(default=None, max_length=1000)
    cancel_url: str | None = Field(default=None, max_length=1000)


class PromptCheckoutSessionResponse(BaseModel):
    url: str
    session_id: str | None = None
    purchase_id: uuid.UUID


class PromptLumenPurchaseRequest(BaseModel):
    client_token: str | None = Field(default=None, min_length=8, max_length=80)


class TrustIndicatorRead(BaseModel):
    key: str
    level: Literal["info", "good", "strong"] = "info"


class MarketplacePayoutRead(BaseModel):
    id: uuid.UUID
    currency_code: str
    status: MarketplacePayoutStatus
    total_amount: int
    purchase_count: int
    external_reference: str | None = None
    requested_at: datetime
    paid_at: datetime | None = None


class MarketplacePayoutRequestWrite(BaseModel):
    currency_code: str = Field(min_length=3, max_length=8)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"RUB", "LMN"}:
            raise ValueError("currency_code must be RUB or LMN")
        return normalized


class MarketplacePayoutFinalizeWrite(BaseModel):
    reference: str | None = Field(default=None, max_length=120)


class PromptReviewReportWrite(BaseModel):
    reason: str = Field(min_length=3, max_length=64)
    details: str | None = Field(default=None, max_length=500)


class SellerMarketplaceSummaryRead(BaseModel):
    rating_average: float | None = None
    rating_display: float | None = None
    review_count: int = 0
    sold_prompts_count: int = 0
    purchases_count: int = 0
    seller_revenue_rub: int = 0
    seller_lumens_earned: int = 0
    pending_balance_rub: int = 0
    available_balance_rub: int = 0
    paid_out_rub: int = 0
    refunded_balance_rub: int = 0
    disputed_balance_rub: int = 0
    pending_balance_lumens: int = 0
    available_balance_lumens: int = 0
    paid_out_lumens: int = 0
    refunded_balance_lumens: int = 0
    disputed_balance_lumens: int = 0
    platform_commission_rub: int = 0
    platform_commission_lumens: int = 0
    clawback_due_rub: int = 0
    clawback_due_lumens: int = 0
    payout_eligible: bool = False
    trust_indicators: list[TrustIndicatorRead] = []
    recent_reviews: list[PromptReviewRead] = []
    recent_payouts: list[MarketplacePayoutRead] = []


class MarketplaceOverviewRead(BaseModel):
    summary: SellerMarketplaceSummaryRead
    purchases: list[PromptPurchaseRead] = []
    reviews: list[PromptReviewRead] = []
    payouts: list[MarketplacePayoutRead] = []
