from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    auth,
    billing,
    categories,
    contributions,
    health,
    lessons,
    moderation,
    prompts,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(billing.router)
api_router.include_router(admin.router)
api_router.include_router(categories.router)
api_router.include_router(prompts.router)
api_router.include_router(lessons.router)
api_router.include_router(contributions.router)
api_router.include_router(moderation.router)
api_router.include_router(users.router)
