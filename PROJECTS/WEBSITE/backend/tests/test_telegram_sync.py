from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.infrastructure.db.models import (
    Category,
    ModerationState,
    PlanTier,
    Prompt,
    PromptStatus,
    PromptTechnique,
    SavedPrompt,
    User,
)
from app.infrastructure.db.session import async_session_maker


TELEGRAM_HEADERS = {"X-Telegram-Bot-Key": "pytest-telegram-bot-sync-key"}


async def _get_user_by_telegram_user_id(telegram_user_id: int) -> User:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        user = result.scalar_one_or_none()
        assert user is not None
        return user


@pytest.mark.asyncio
async def test_telegram_upsert_requires_internal_key(async_client):
    response = await async_client.post(
        "/api/v1/telegram/users/upsert",
        json={
            "telegram_user_id": 1001,
            "username": "jake",
            "first_name": "Jake",
            "language": "en",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == "telegram_sync_unauthorized"


@pytest.mark.asyncio
async def test_telegram_upsert_creates_synthetic_site_user(async_client):
    response = await async_client.post(
        "/api/v1/telegram/users/upsert",
        headers=TELEGRAM_HEADERS,
        json={
            "telegram_user_id": 1002,
            "username": "jake_firstman",
            "first_name": "Jake",
            "last_name": "Firstman",
            "language": "en",
            "is_active": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_user_id"] == 1002
    assert payload["display_name"] == "Jake Firstman"
    assert payload["language"] == "eng"
    assert payload["plan_tier"] == "free"
    assert payload["is_premium"] is False

    user = await _get_user_by_telegram_user_id(1002)
    assert user.email == "tg_1002@telegram.local"
    assert user.telegram_username == "jake_firstman"
    assert user.telegram_language == "eng"
    assert user.telegram_is_active is True


@pytest.mark.asyncio
async def test_telegram_profile_reports_saved_and_authored_counts(async_client):
    create_user = await async_client.post(
        "/api/v1/telegram/users/upsert",
        headers=TELEGRAM_HEADERS,
        json={
            "telegram_user_id": 1003,
            "username": "profile_user",
            "first_name": "Profile",
            "language": "ru",
            "is_active": True,
        },
    )
    assert create_user.status_code == 200
    user = await _get_user_by_telegram_user_id(1003)

    async with async_session_maker() as session:
        category = Category(slug="telegram-profile-it", name="IT", sort_order=0, is_restricted=False)
        session.add(category)
        await session.flush()

        authored_prompt = Prompt(
            slug="telegram-profile-authored",
            title="Telegram authored",
            body="authored prompt body",
            summary="authored prompt body",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            is_premium=False,
            category_id=category.id,
            author_id=user.id,
            auto_approved=True,
            created_at=datetime.now(timezone.utc),
            legacy_bot_prompt_id=9001,
            legacy_bot_category="it",
            legacy_bot_subcategory="sub_it_docs_ru",
            content_language="ru",
        )
        saved_prompt = Prompt(
            slug="telegram-profile-saved",
            title="Telegram saved",
            body="saved prompt body",
            summary="saved prompt body",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            is_premium=False,
            category_id=category.id,
            author_id=None,
            auto_approved=True,
            created_at=datetime.now(timezone.utc),
            legacy_bot_prompt_id=9002,
            legacy_bot_category="it",
            legacy_bot_subcategory="sub_it_docs_ru",
            content_language="ru",
        )
        session.add_all([authored_prompt, saved_prompt])
        await session.flush()
        session.add(SavedPrompt(user_id=user.id, prompt_id=saved_prompt.id))
        await session.commit()

    profile = await async_client.get(
        "/api/v1/telegram/users/1003/profile",
        headers=TELEGRAM_HEADERS,
    )
    assert profile.status_code == 200
    payload = profile.json()
    assert payload["prompts_submitted"] == 1
    assert payload["prompts_saved"] == 1
    assert payload["days_in_bot"] >= 1


@pytest.mark.asyncio
async def test_telegram_subcategory_prompts_apply_premium_gating(async_client):
    create_user = await async_client.post(
        "/api/v1/telegram/users/upsert",
        headers=TELEGRAM_HEADERS,
        json={
            "telegram_user_id": 1004,
            "username": "premium_gate",
            "first_name": "Premium",
            "language": "ru",
            "is_active": True,
        },
    )
    assert create_user.status_code == 200
    user = await _get_user_by_telegram_user_id(1004)

    premium_body = "x" * 400

    async with async_session_maker() as session:
        category = Category(slug="telegram-it", name="Telegram IT", sort_order=0, is_restricted=False)
        session.add(category)
        await session.flush()

        free_prompt = Prompt(
            slug="telegram-free-prompt",
            title="Free prompt",
            body="free prompt body",
            summary="free prompt body",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            is_premium=False,
            category_id=category.id,
            author_id=None,
            auto_approved=True,
            created_at=datetime.now(timezone.utc),
            legacy_bot_prompt_id=9101,
            legacy_bot_category="it",
            legacy_bot_subcategory="sub_it_code_ru",
            content_language="ru",
        )
        premium_prompt = Prompt(
            slug="telegram-premium-prompt",
            title="Premium prompt",
            body=premium_body,
            summary=premium_body[:120],
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            is_premium=True,
            category_id=category.id,
            author_id=None,
            auto_approved=True,
            created_at=datetime.now(timezone.utc),
            legacy_bot_prompt_id=9102,
            legacy_bot_category="it",
            legacy_bot_subcategory="sub_it_code_ru",
            content_language="ru",
        )
        session.add_all([free_prompt, premium_prompt])
        await session.commit()

    response = await async_client.get(
        "/api/v1/telegram/subcategories/sub_it_code_ru/prompts",
        headers=TELEGRAM_HEADERS,
        params={"language": "ru", "telegram_user_id": 1004},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2

    premium_item = next(item for item in payload if item["legacy_bot_prompt_id"] == 9102)
    assert premium_item["body_locked"] is True
    assert premium_item["body"] != premium_body

    async with async_session_maker() as session:
        db_user = await session.get(User, user.id)
        assert db_user is not None
        db_user.plan_tier = PlanTier.starter
        await session.commit()

    unlocked = await async_client.get(
        "/api/v1/telegram/subcategories/sub_it_code_ru/prompts",
        headers=TELEGRAM_HEADERS,
        params={"language": "ru", "telegram_user_id": 1004},
    )
    assert unlocked.status_code == 200
    unlocked_payload = unlocked.json()
    premium_item = next(item for item in unlocked_payload if item["legacy_bot_prompt_id"] == 9102)
    assert premium_item["body_locked"] is False
    assert premium_item["body"] == premium_body
