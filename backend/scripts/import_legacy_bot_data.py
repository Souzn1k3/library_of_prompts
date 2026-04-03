from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
import re
import uuid

import asyncpg
from sqlalchemy import select

from app.config import get_settings
from app.infrastructure.db.models import (
    Category,
    ModerationState,
    Prompt,
    PromptStatus,
    PromptTechnique,
    SavedPrompt,
)
from app.infrastructure.db.session import async_session_maker
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.telegram_sync.model.telegram import TelegramUserUpsert, normalize_language_code
from app.modules.telegram_sync.repository.telegram_repository import TelegramSyncRepository
from app.modules.telegram_sync.service.telegram_service import TelegramSyncService


_CATEGORY_NAMES: dict[str, str] = {
    "it": "Информационные технологии и Разработка ПО",
    "marketing": "Маркетинг, Реклама и PR",
    "business": "Бизнес, Менеджмент и Предпринимательство",
    "education": "Образование и Наука",
    "arts": "Творчество, Искусство и Медиа",
    "engineering": "Инженерия, Строительство и Производство",
    "finance": "Финансы, Банкинг и Страхование",
    "law": "Государственное управление и Право",
    "agro": "Сельское хозяйство и Экология",
    "logistics": "Логистика, Транспорт и Туризм",
    "real_estate": "Недвижимость",
    "lifestyle": "Персональная эффективность и Lifestyle",
    "niche": "Специализированные и Нишевые области",
}


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "bot-prompt"


def _prompt_slug(*, title: str, language: str, legacy_id: int) -> str:
    base = _slugify(title)
    if not base:
        base = "bot-prompt"
    return f"{base}-{language}-{legacy_id}"


def _summary(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    snippet = stripped[:500]
    return snippet or None


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fallback_title(row: Mapping[str, object]) -> str:
    subcategory = str(row.get("subcategory") or "legacy-section").strip() or "legacy-section"
    language = normalize_language_code(str(row.get("language") or "ru"))
    prompt_id = int(row.get("id") or 0)
    return f"{subcategory} #{prompt_id} [{language}]"


async def _ensure_category(
    repo: TelegramSyncRepository,
    *,
    legacy_category: str,
) -> Category:
    slug = legacy_category.replace("_", "-").strip().lower()
    name = _CATEGORY_NAMES.get(legacy_category, legacy_category.replace("_", " ").strip().title())
    existing = await repo.get_category_by_slug(slug)
    if existing is not None:
        return existing
    return await repo.create_category(Category(slug=slug, name=name, sort_order=0, is_restricted=False))


async def _prompt_slug_available(slug: str, prompt_id: uuid.UUID | None = None) -> bool:
    async with async_session_maker() as session:
        stmt = select(Prompt).where(Prompt.slug == slug)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            return True
        if prompt_id is not None and existing.id == prompt_id:
            return True
        return False


async def _unique_prompt_slug(
    *,
    title: str,
    language: str,
    legacy_id: int,
    current_id: uuid.UUID | None = None,
) -> str:
    base = _prompt_slug(title=title, language=language, legacy_id=legacy_id)
    if await _prompt_slug_available(base, prompt_id=current_id):
        return base
    suffix = 2
    while True:
        candidate = f"{base}-{suffix}"
        if await _prompt_slug_available(candidate, prompt_id=current_id):
            return candidate
        suffix += 1


async def import_legacy_bot_data() -> None:
    settings = get_settings()
    legacy_url = settings.legacy_bot_database_url
    if not legacy_url:
        raise RuntimeError("LEGACY_BOT_DATABASE_URL is required for legacy bot import.")

    legacy_conn = await asyncpg.connect(legacy_url)
    try:
        legacy_users = await legacy_conn.fetch(
            """
            SELECT user_id, username, first_name, last_name, language, is_premium, is_active, joined_at, last_active
            FROM users
            ORDER BY joined_at, user_id
            """
        )
        legacy_prompts = await legacy_conn.fetch(
            """
            SELECT id, category, subcategory, language, title, content, is_premium, created_at
            FROM prompts
            ORDER BY id
            """
        )
        legacy_saved = await legacy_conn.fetch(
            """
            SELECT user_id, prompt_id
            FROM user_saved_prompts
            ORDER BY user_id, prompt_id
            """
        )
    finally:
        await legacy_conn.close()

    async with async_session_maker() as session:
        tg_repo = TelegramSyncRepository(session)
        tg_service = TelegramSyncService(tg_repo)
        prompt_repo = PromptRepository(session)

        user_map: dict[int, uuid.UUID] = {}
        prompt_map: dict[int, uuid.UUID] = {}

        for row in legacy_users:
            payload = TelegramUserUpsert(
                telegram_user_id=int(row["user_id"]),
                username=row["username"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                language=normalize_language_code(str(row["language"] or "ru")),
                is_active=bool(row["is_active"]),
            )
            profile = await tg_service.upsert_user(
                payload,
                imported_is_premium=bool(row["is_premium"]),
                imported_joined_at=_aware(row["joined_at"]),
                imported_last_active=_aware(row["last_active"]),
            )
            user_map[int(row["user_id"])] = profile.user_id

        for row in legacy_prompts:
            legacy_id = int(row["id"])
            legacy_category = str(row["category"] or "niche").strip().lower()
            language = normalize_language_code(str(row["language"] or "ru"))
            category = await _ensure_category(tg_repo, legacy_category=legacy_category)

            prompt = await tg_repo.get_prompt_by_legacy_bot_prompt_id(legacy_id)
            title = str(row["title"] or _fallback_title(row))
            body = str(row["content"] or "").strip()
            if not body:
                continue

            created_at = _aware(row["created_at"]) or datetime.now(timezone.utc)

            if prompt is None:
                prompt = Prompt(
                    slug=await _unique_prompt_slug(title=title, language=language, legacy_id=legacy_id),
                    title=title,
                    body=body,
                    summary=_summary(body),
                    status=PromptStatus.published,
                    technique=PromptTechnique.other,
                    moderation_state=ModerationState.approved,
                    is_premium=bool(row["is_premium"]),
                    category_id=category.id,
                    author_id=None,
                    moderated_by_id=None,
                    moderated_at=created_at,
                    auto_approved=True,
                    created_at=created_at,
                    legacy_bot_prompt_id=legacy_id,
                    legacy_bot_category=legacy_category,
                    legacy_bot_subcategory=str(row["subcategory"] or "").strip() or None,
                    content_language=language,
                )
                prompt = await tg_repo.create_prompt(prompt)
            else:
                prompt.slug = await _unique_prompt_slug(
                    title=title,
                    language=language,
                    legacy_id=legacy_id,
                    current_id=prompt.id,
                )
                prompt.title = title
                prompt.body = body
                prompt.summary = _summary(body)
                prompt.status = PromptStatus.published
                prompt.technique = PromptTechnique.other
                prompt.moderation_state = ModerationState.approved
                prompt.is_premium = bool(row["is_premium"])
                prompt.category_id = category.id
                prompt.moderated_at = created_at
                prompt.auto_approved = True
                prompt.legacy_bot_category = legacy_category
                prompt.legacy_bot_subcategory = str(row["subcategory"] or "").strip() or None
                prompt.content_language = language
                prompt = await tg_repo.save_prompt(prompt)

            await prompt_repo.ensure_prompt_stats(prompt.id)
            prompt_map[legacy_id] = prompt.id

        saved_inserted = 0
        for row in legacy_saved:
            user_id = user_map.get(int(row["user_id"]))
            prompt_id = prompt_map.get(int(row["prompt_id"]))
            if user_id is None or prompt_id is None:
                continue

            existing = await session.execute(
                select(SavedPrompt).where(
                    SavedPrompt.user_id == user_id,
                    SavedPrompt.prompt_id == prompt_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            saved = SavedPrompt(user_id=user_id, prompt_id=prompt_id)
            session.add(saved)
            await session.flush()
            await prompt_repo.adjust_save_count(prompt_id, 1)
            saved_inserted += 1

        await session.commit()

    print(
        "Imported legacy bot data:",
        f"users={len(user_map)}",
        f"prompts={len(prompt_map)}",
        f"saved_links={saved_inserted}",
    )


if __name__ == "__main__":
    asyncio.run(import_legacy_bot_data())
