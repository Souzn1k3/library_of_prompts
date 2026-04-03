import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.infrastructure.db.models import Category, Prompt, PromptStatus, SavedPrompt, User


class TelegramSyncRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def list_active_telegram_users(self) -> Sequence[User]:
        result = await self._session.execute(
            select(User)
            .where(
                User.telegram_user_id.is_not(None),
                User.telegram_is_active.is_(True),
            )
            .order_by(User.telegram_joined_at.asc().nullslast(), User.created_at.asc())
        )
        return result.scalars().all()

    async def create_user(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def save_user(self, user: User) -> User:
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def count_saved_prompts(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(SavedPrompt).where(SavedPrompt.user_id == user_id)
        )
        return int(result.scalar_one() or 0)

    async def count_authored_prompts(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Prompt).where(Prompt.author_id == user_id)
        )
        return int(result.scalar_one() or 0)

    async def list_published_bot_prompts(
        self,
        *,
        subcategory_key: str,
        language: str,
    ) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .options(joinedload(Prompt.category))
            .where(
                Prompt.status == PromptStatus.published,
                Prompt.legacy_bot_subcategory == subcategory_key,
                Prompt.content_language == language,
            )
            .order_by(Prompt.legacy_bot_prompt_id.asc(), Prompt.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_category_by_slug(self, slug: str) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def create_category(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def get_prompt_by_legacy_bot_prompt_id(self, legacy_bot_prompt_id: int) -> Prompt | None:
        result = await self._session.execute(
            select(Prompt).where(Prompt.legacy_bot_prompt_id == legacy_bot_prompt_id)
        )
        return result.scalar_one_or_none()

    async def create_prompt(self, prompt: Prompt) -> Prompt:
        self._session.add(prompt)
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt

    async def save_prompt(self, prompt: Prompt) -> Prompt:
        await self._session.flush()
        await self._session.refresh(prompt)
        return prompt
