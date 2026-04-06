from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    analytics,
    auth,
    billing,
    categories,
    store,
    wallet,
    learning,
    contributors,
    contributions,
    health,
    lessons,
    marketplace,
    missions,
    moderation,
    onboarding,
    prompts,
    scenarios,
    telegram,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(analytics.router)
api_router.include_router(billing.router)
api_router.include_router(admin.router)
api_router.include_router(categories.router)
api_router.include_router(store.router)
api_router.include_router(wallet.router)
api_router.include_router(contributors.router)
api_router.include_router(marketplace.router)
api_router.include_router(prompts.router)
api_router.include_router(scenarios.router)
api_router.include_router(learning.router)
api_router.include_router(lessons.router)
api_router.include_router(missions.router)
api_router.include_router(onboarding.router)
api_router.include_router(contributions.router)
api_router.include_router(moderation.router)
api_router.include_router(users.router)
api_router.include_router(telegram.router)
