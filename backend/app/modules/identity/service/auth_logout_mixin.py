import uuid
from datetime import datetime, timezone

from app.modules.identity.service.auth_helpers import hash_refresh_token


class AuthLogoutMixin:
    async def logout(
        self,
        *,
        refresh_token: str | None,
        user_id: uuid.UUID | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        if refresh_token:
            row = await self._refresh_tokens.get_by_token_hash(hash_refresh_token(refresh_token))
            if row is not None and row.revoked_at is None:
                await self._refresh_tokens.revoke(
                    row,
                    reason="logout",
                    revoked_at=now,
                )
                return

        if user_id is not None:
            await self._refresh_tokens.revoke_all_for_user(
                user_id=user_id,
                reason="logout_all",
                revoked_at=now,
            )
