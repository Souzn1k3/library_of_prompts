import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.infrastructure.db.models import AuthRefreshToken, User
from app.modules.identity.model.auth import SessionTokens
from app.modules.identity.service.auth_helpers import hash_refresh_token, new_refresh_token_pair


class AuthSessionMixin:
    async def _issue_session_tokens(
        self,
        *,
        user: User,
        client_ip: str | None,
        user_agent: str | None,
        family_id: uuid.UUID | None = None,
    ) -> tuple[SessionTokens, AuthRefreshToken]:
        now = datetime.now(timezone.utc)
        refresh_expires_at = now + timedelta(days=self._settings.refresh_token_expire_days)
        token_jti, refresh_token = new_refresh_token_pair()
        refresh_row = AuthRefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            token_jti=token_jti,
            family_id=family_id or uuid.uuid4(),
            expires_at=refresh_expires_at,
            revoked_at=None,
            revoked_reason=None,
            replaced_by_token_id=None,
            created_ip=(client_ip or "")[:64] or None,
            user_agent=(user_agent or "")[:255] or None,
            last_used_at=now,
        )
        refresh_row = await self._refresh_tokens.create(refresh_row)
        access_token = create_access_token(subject_user_id=user.id)
        return SessionTokens(access_token=access_token, refresh_token=refresh_token), refresh_row
