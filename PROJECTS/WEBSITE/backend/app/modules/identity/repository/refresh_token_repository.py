import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AuthRefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, row: AuthRefreshToken) -> AuthRefreshToken:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_by_token_hash(self, token_hash: str) -> AuthRefreshToken | None:
        result = await self._session.execute(
            select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, token_id: uuid.UUID) -> AuthRefreshToken | None:
        result = await self._session.execute(
            select(AuthRefreshToken).where(AuthRefreshToken.id == token_id)
        )
        return result.scalar_one_or_none()

    async def save(self, row: AuthRefreshToken) -> AuthRefreshToken:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def revoke(
        self,
        row: AuthRefreshToken,
        *,
        reason: str,
        revoked_at: datetime,
        replaced_by_token_id: uuid.UUID | None = None,
    ) -> AuthRefreshToken:
        row.revoked_at = revoked_at
        row.revoked_reason = reason
        row.replaced_by_token_id = replaced_by_token_id
        return await self.save(row)

    async def revoke_family(
        self,
        *,
        family_id: uuid.UUID,
        reason: str,
        revoked_at: datetime,
    ) -> int:
        stmt = (
            update(AuthRefreshToken)
            .where(
                AuthRefreshToken.family_id == family_id,
                AuthRefreshToken.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                revoked_reason=reason,
                updated_at=revoked_at,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def revoke_all_for_user(
        self,
        *,
        user_id: uuid.UUID,
        reason: str,
        revoked_at: datetime,
    ) -> int:
        stmt = (
            update(AuthRefreshToken)
            .where(
                AuthRefreshToken.user_id == user_id,
                AuthRefreshToken.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                revoked_reason=reason,
                updated_at=revoked_at,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

