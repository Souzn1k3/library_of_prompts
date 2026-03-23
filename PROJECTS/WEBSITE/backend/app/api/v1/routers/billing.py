from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans")
async def list_plans() -> list[dict[str, object]]:
    return [
        {
            "tier": "free",
            "name": "Free",
            "price_usd_month": 0,
            "features": ["Browse catalog", "Save prompts", "Community submissions"],
        },
        {
            "tier": "starter",
            "name": "Starter",
            "price_usd_month": 9,
            "features": ["Premium prompt bodies", "Email support"],
        },
        {
            "tier": "pro",
            "name": "Pro",
            "price_usd_month": 29,
            "features": ["Restricted categories", "Full lesson library", "Priority moderation"],
        },
        {
            "tier": "enterprise",
            "name": "Enterprise",
            "price_usd_month": 99,
            "features": ["Team seats", "SSO (roadmap)", "Custom agreements"],
        },
    ]


@router.post("/checkout")
async def checkout_stub() -> None:
    raise HTTPException(
        status_code=501,
        detail="Stripe checkout is not configured. Use admin tier override in development.",
    )
