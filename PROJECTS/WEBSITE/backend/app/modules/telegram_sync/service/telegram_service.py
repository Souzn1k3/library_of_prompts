from __future__ import annotations

from datetime import datetime, timezone
import secrets

from app.core.errors import NotFoundError
from app.core.security import hash_password
from app.core.tiers import can_view_premium_content, mask_body_if_needed
from app.infrastructure.db.models import PlanTier, Prompt, User
from app.modules.telegram_sync.model.telegram import (
    TelegramActiveUserRead,
    TelegramProfileRead,
    TelegramPromptRead,
    TelegramUserUpsert,
)
from app.modules.telegram_sync.repository.telegram_repository import TelegramSyncRepository


def _synthetic_email(telegram_user_id: int) -> str:
    return f"tg_{telegram_user_id}@telegram.local"


def _is_synthetic_email(email: str) -> bool:
    return email.lower().endswith("@telegram.local")


def _build_display_name(*, username: str | None, first_name: str | None, last_name: str | None, telegram_user_id: int) -> str:
    full_name = " ".join([part for part in [first_name, last_name] if part]).strip()
    if full_name:
        return full_name[:120]
    if username:
        return username[:120]
    return f"Telegram User {telegram_user_id}"


def _days_since(dt: datetime) -> int:
    source = dt
    if source.tzinfo is None:
        source = source.replace(tzinfo=timezone.utc)
    else:
        source = source.astimezone(timezone.utc)
    delta = datetime.now(timezone.utc) - source
    return max(int(delta.total_seconds() // 86400) + 1, 1)


class TelegramSyncService:
    def __init__(self, repo: TelegramSyncRepository) -> None:
        self._repo = repo

    async def _profile_from_user(self, user: User) -> TelegramProfileRead:
        joined_at = user.telegram_joined_at or user.created_at
        prompts_saved = await self._repo.count_saved_prompts(user.id)
        prompts_submitted = await self._repo.count_authored_prompts(user.id)
        return TelegramProfileRead(
            user_id=user.id,
            telegram_user_id=int(user.telegram_user_id or 0),
            display_name=user.display_name,
            username=user.telegram_username,
            first_name=user.telegram_first_name,
            last_name=user.telegram_last_name,
            language=user.telegram_language or "ru",
            plan_tier=user.plan_tier,
            is_premium=can_view_premium_content(user),
            is_active=user.telegram_is_active,
            joined_at=joined_at,
            last_active=user.telegram_last_active,
            prompts_submitted=prompts_submitted,
            prompts_saved=prompts_saved,
            days_in_bot=_days_since(joined_at),
        )

    async def upsert_user(
        self,
        data: TelegramUserUpsert,
        *,
        imported_is_premium: bool = False,
        imported_joined_at: datetime | None = None,
        imported_last_active: datetime | None = None,
    ) -> TelegramProfileRead:
        user = await self._repo.get_user_by_telegram_user_id(data.telegram_user_id)
        synthetic_email = _synthetic_email(data.telegram_user_id)
        now = datetime.now(timezone.utc)
        joined_at = imported_joined_at or now
        last_active = imported_last_active or now

        if user is None:
            user = await self._repo.get_user_by_email(synthetic_email)

        display_name = _build_display_name(
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            telegram_user_id=data.telegram_user_id,
        )

        if user is None:
            user = User(
                email=synthetic_email,
                hashed_password=hash_password(secrets.token_urlsafe(24)),
                display_name=display_name,
                plan_tier=PlanTier.starter if imported_is_premium else PlanTier.free,
                telegram_user_id=data.telegram_user_id,
                telegram_username=data.username,
                telegram_first_name=data.first_name,
                telegram_last_name=data.last_name,
                telegram_language=data.language,
                telegram_is_active=data.is_active,
                telegram_joined_at=joined_at,
                telegram_last_active=last_active,
            )
            user = await self._repo.create_user(user)
            return await self._profile_from_user(user)

        user.telegram_user_id = data.telegram_user_id
        if data.username is not None:
            user.telegram_username = data.username
        if data.first_name is not None:
            user.telegram_first_name = data.first_name
        if data.last_name is not None:
            user.telegram_last_name = data.last_name
        user.telegram_language = data.language
        user.telegram_is_active = data.is_active
        if user.telegram_joined_at is None:
            user.telegram_joined_at = joined_at
        user.telegram_last_active = last_active
        if imported_is_premium and user.plan_tier == PlanTier.free:
            user.plan_tier = PlanTier.starter
        if _is_synthetic_email(user.email):
            user.display_name = display_name

        user = await self._repo.save_user(user)
        return await self._profile_from_user(user)

    async def get_profile(self, telegram_user_id: int) -> TelegramProfileRead:
        user = await self._repo.get_user_by_telegram_user_id(telegram_user_id)
        if user is None:
            raise NotFoundError("telegram_user", str(telegram_user_id))
        return await self._profile_from_user(user)

    async def list_active_users(self) -> list[TelegramActiveUserRead]:
        rows = await self._repo.list_active_telegram_users()
        return [
            TelegramActiveUserRead(
                telegram_user_id=int(row.telegram_user_id or 0),
                language=row.telegram_language or "ru",
                first_name=row.telegram_first_name,
            )
            for row in rows
            if row.telegram_user_id is not None
        ]

    async def list_prompts(
        self,
        *,
        subcategory_key: str,
        language: str,
        telegram_user_id: int | None = None,
    ) -> list[TelegramPromptRead]:
        viewer = None
        if telegram_user_id is not None:
            viewer = await self._repo.get_user_by_telegram_user_id(telegram_user_id)

        rows = await self._repo.list_published_bot_prompts(
            subcategory_key=subcategory_key,
            language=language,
        )
        return [self._to_prompt_read(row, viewer=viewer) for row in rows]

    def _to_prompt_read(self, row: Prompt, *, viewer: User | None) -> TelegramPromptRead:
        locked = bool(row.is_premium) and not can_view_premium_content(viewer)
        return TelegramPromptRead(
            id=row.id,
            legacy_bot_prompt_id=row.legacy_bot_prompt_id,
            slug=row.slug,
            title=row.title,
            body=mask_body_if_needed(body=row.body, locked=locked),
            body_locked=locked,
            is_premium=row.is_premium,
            legacy_bot_category=row.legacy_bot_category,
            legacy_bot_subcategory=row.legacy_bot_subcategory,
            content_language=row.content_language,
            created_at=row.created_at,
        )
