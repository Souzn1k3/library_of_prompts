from __future__ import annotations

from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service_deps import get_wallet_service
from app.config import get_settings
from app.core.errors import AppError
from app.infrastructure.db.session import get_db
from app.modules.economy.service.wallet_service import WalletService
from app.modules.telegram_sync.model.telegram import (
    TelegramActiveUserRead,
    TelegramProfileRead,
    TelegramPromptRead,
    TelegramRewardClaimRead,
    TelegramRewardClaimWrite,
    TelegramUserUpsert,
    normalize_language_code,
)
from app.modules.telegram_sync.repository.telegram_repository import TelegramSyncRepository
from app.modules.telegram_sync.service.telegram_reward_service import TelegramRewardService
from app.modules.telegram_sync.service.telegram_service import TelegramSyncService


def require_telegram_bot_key(
    x_telegram_bot_key: str | None = Header(default=None, alias="X-Telegram-Bot-Key"),
) -> None:
    expected = get_settings().telegram_bot_api_key
    if not expected:
        raise AppError(
            code="telegram_sync_not_configured",
            message="Telegram sync is not configured.",
            status_code=503,
        )
    if not x_telegram_bot_key or not compare_digest(x_telegram_bot_key, expected):
        raise AppError(
            code="telegram_sync_unauthorized",
            message="Telegram sync key is invalid.",
            status_code=401,
        )


router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
    dependencies=[Depends(require_telegram_bot_key)],
)


def telegram_service(session: AsyncSession = Depends(get_db)) -> TelegramSyncService:
    return TelegramSyncService(TelegramSyncRepository(session))


def telegram_reward_service(
    session: AsyncSession = Depends(get_db),
    wallet: WalletService = Depends(get_wallet_service),
) -> TelegramRewardService:
    return TelegramRewardService(
        repo=TelegramSyncRepository(session),
        wallet=wallet,
        settings=get_settings(),
    )


@router.post("/users/upsert", response_model=TelegramProfileRead)
async def upsert_telegram_user(
    body: TelegramUserUpsert,
    svc: TelegramSyncService = Depends(telegram_service),
) -> TelegramProfileRead:
    return await svc.upsert_user(body)


@router.get("/users/{telegram_user_id}/profile", response_model=TelegramProfileRead)
async def telegram_profile(
    telegram_user_id: int,
    svc: TelegramSyncService = Depends(telegram_service),
) -> TelegramProfileRead:
    return await svc.get_profile(telegram_user_id)


@router.get("/users/active", response_model=list[TelegramActiveUserRead])
async def telegram_active_users(
    svc: TelegramSyncService = Depends(telegram_service),
) -> list[TelegramActiveUserRead]:
    return await svc.list_active_users()


@router.get("/subcategories/{subcategory_key}/prompts", response_model=list[TelegramPromptRead])
async def telegram_prompts_by_subcategory(
    subcategory_key: str,
    language: str = Query(default="ru", min_length=2, max_length=10),
    telegram_user_id: int | None = Query(default=None, gt=0),
    svc: TelegramSyncService = Depends(telegram_service),
) -> list[TelegramPromptRead]:
    return await svc.list_prompts(
        subcategory_key=subcategory_key,
        language=normalize_language_code(language),
        telegram_user_id=telegram_user_id,
    )


@router.post("/rewards/claim", response_model=TelegramRewardClaimRead)
async def telegram_claim_reward(
    body: TelegramRewardClaimWrite,
    svc: TelegramRewardService = Depends(telegram_reward_service),
) -> TelegramRewardClaimRead:
    return await svc.claim_reward(body)
