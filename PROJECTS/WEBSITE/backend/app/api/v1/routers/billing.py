from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.core.errors import AppError
from app.core.i18n import resolve_language_from_header
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.billing.model.billing import (
    BillingPortalRequest,
    BillingPortalResponse,
    BillingStatusRead,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PlanPublicRead,
)
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.billing.service.billing_service import BillingService
from app.modules.billing.service.entitlement_service import EntitlementService
from app.modules.identity.repository.user_repository import UserRepository

router = APIRouter(prefix="/billing", tags=["billing"])


def billing_service(session: AsyncSession = Depends(get_db)) -> BillingService:
    billing_repo = BillingRepository(session)
    user_repo = UserRepository(session)
    entitlements = EntitlementService(billing_repo, user_repo)
    analytics = AnalyticsService(AnalyticsRepository(session))
    return BillingService(
        billing_repo,
        entitlements,
        user_repo,
        get_settings(),
        analytics=analytics,
    )


@router.get("/plans", response_model=list[PlanPublicRead])
async def list_plans(
    request: Request,
    svc: BillingService = Depends(billing_service),
) -> list[PlanPublicRead]:
    language = resolve_language_from_header(request.headers.get("accept-language"))
    return await svc.list_public_plans(language)


@router.get("/subscription", response_model=BillingStatusRead)
async def subscription_status(
    current_user: User = Depends(get_current_user),
    svc: BillingService = Depends(billing_service),
) -> BillingStatusRead:
    return await svc.get_subscription_status(current_user)


@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    svc: BillingService = Depends(billing_service),
) -> CheckoutSessionResponse:
    return await svc.create_checkout_session(user=current_user, payload=body)


@router.post("/checkout")
async def deprecated_checkout_endpoint() -> None:
    raise AppError(
        code="deprecated_endpoint",
        status_code=410,
        message="This action is no longer available.",
    )


@router.post("/portal", response_model=BillingPortalResponse)
async def create_portal_session(
    body: BillingPortalRequest,
    current_user: User = Depends(get_current_user),
    svc: BillingService = Depends(billing_service),
) -> BillingPortalResponse:
    return await svc.create_portal_session(user=current_user, payload=body)


@router.post("/webhooks")
async def handle_webhook(
    request: Request,
    svc: BillingService = Depends(billing_service),
) -> dict[str, str]:
    payload = await request.body()
    signature_header = request.headers.get("stripe-signature")
    return await svc.handle_webhook(payload=payload, signature_header=signature_header)
