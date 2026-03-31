import uuid

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.api.service_deps import get_marketplace_service
from app.core.rate_limit import enforce_rate_limit, resolve_rate_limit_ip
from app.infrastructure.db.models import User
from app.modules.marketplace.model.marketplace import (
    MarketplacePayoutRead,
    MarketplacePayoutRequestWrite,
    MarketplaceOverviewRead,
    PromptCheckoutSessionRequest,
    PromptCheckoutSessionResponse,
    PromptLumenPurchaseRequest,
    PromptPurchaseActionResponse,
    PromptReviewRead,
    PromptReviewReportWrite,
    PromptReviewWrite,
)
from app.modules.marketplace.service.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/me", response_model=MarketplaceOverviewRead)
async def marketplace_me(
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplaceOverviewRead:
    reputation_tier = current_user.contributor_profile.reputation_tier.value if current_user.contributor_profile else None
    return await svc.overview_for_user(current_user, reputation_tier=reputation_tier)


@router.post("/payouts/request", response_model=MarketplacePayoutRead)
async def request_marketplace_payout(
    request: Request,
    body: MarketplacePayoutRequestWrite,
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplacePayoutRead:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(key=f"marketplace:payout:user:{current_user.id}", limit=8, window_seconds=10 * 60)
    await enforce_rate_limit(key=f"marketplace:payout:ip:{ip}", limit=16, window_seconds=10 * 60)
    return await svc.create_payout_batch(
        seller_user_id=current_user.id,
        currency_code=body.currency_code,
        notes=body.notes.strip() if body.notes else None,
    )


@router.post("/prompts/{prompt_id}/buy-with-lumens", response_model=PromptPurchaseActionResponse)
async def buy_prompt_with_lumens(
    request: Request,
    prompt_id: uuid.UUID,
    body: PromptLumenPurchaseRequest | None = None,
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> PromptPurchaseActionResponse:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(key=f"marketplace:lumen:user:{current_user.id}", limit=20, window_seconds=10 * 60)
    await enforce_rate_limit(key=f"marketplace:lumen:ip:{ip}", limit=35, window_seconds=10 * 60)
    prompt = await svc.get_prompt_or_404(prompt_id)
    return await svc.purchase_with_lumens(
        user=current_user,
        prompt=prompt,
        payload=body or PromptLumenPurchaseRequest(),
    )


@router.post("/prompts/checkout-session", response_model=PromptCheckoutSessionResponse)
async def create_prompt_checkout_session(
    request: Request,
    body: PromptCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> PromptCheckoutSessionResponse:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(key=f"marketplace:checkout:user:{current_user.id}", limit=20, window_seconds=10 * 60)
    await enforce_rate_limit(key=f"marketplace:checkout:ip:{ip}", limit=35, window_seconds=10 * 60)
    return await svc.create_checkout_session(user=current_user, payload=body)


@router.put("/prompts/{prompt_id}/review", response_model=PromptReviewRead)
async def upsert_prompt_review(
    request: Request,
    prompt_id: uuid.UUID,
    body: PromptReviewWrite,
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> PromptReviewRead:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(key=f"marketplace:review:user:{current_user.id}", limit=30, window_seconds=10 * 60)
    await enforce_rate_limit(key=f"marketplace:review:ip:{ip}", limit=45, window_seconds=10 * 60)
    return await svc.upsert_review(user=current_user, prompt_id=prompt_id, payload=body)


@router.post("/reviews/{review_id}/report", response_model=PromptReviewRead)
async def report_prompt_review(
    request: Request,
    review_id: uuid.UUID,
    body: PromptReviewReportWrite,
    current_user: User = Depends(get_current_user),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> PromptReviewRead:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(key=f"marketplace:report:user:{current_user.id}", limit=20, window_seconds=10 * 60)
    await enforce_rate_limit(key=f"marketplace:report:ip:{ip}", limit=35, window_seconds=10 * 60)
    return await svc.report_review(user=current_user, review_id=review_id, payload=body)
