from datetime import datetime, timezone

from app.core.errors import AppError
from app.core.logging import get_logger
from app.modules.identity.model.auth import SessionTokens
from app.modules.identity.service.auth_helpers import as_utc, hash_refresh_token

log = get_logger(__name__)


class AuthRefreshMixin:
    async def refresh_session(
        self,
        *,
        refresh_token: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> SessionTokens:
        now = datetime.now(timezone.utc)
        row = await self._refresh_tokens.get_by_token_hash(
            hash_refresh_token(refresh_token),
            for_update=True,
        )
        if row is None:
            log.warning(
                "auth_refresh_failed",
                observability_event="auth_refresh_failed",
                reason="token_not_found",
                client_ip=client_ip,
            )
            raise AppError(
                code="invalid_refresh_token",
                message="Your session has ended. Please log in again.",
                status_code=401,
            )

        if row.revoked_at is not None:
            if row.replaced_by_token_id is not None:
                await self._refresh_tokens.revoke_family(
                    family_id=row.family_id,
                    reason="refresh_reuse_detected",
                    revoked_at=now,
                )
            log.warning(
                "auth_refresh_failed",
                observability_event="auth_refresh_failed",
                reason="token_reused",
                user_id=str(row.user_id),
                client_ip=client_ip,
            )
            raise AppError(
                code="refresh_token_reused",
                message="Your session has ended. Please log in again.",
                status_code=401,
            )

        expires_at = as_utc(row.expires_at)
        if expires_at <= now:
            await self._refresh_tokens.revoke(
                row,
                reason="refresh_expired",
                revoked_at=now,
            )
            log.warning(
                "auth_refresh_failed",
                observability_event="auth_refresh_failed",
                reason="token_expired",
                user_id=str(row.user_id),
                client_ip=client_ip,
            )
            raise AppError(
                code="refresh_token_expired",
                message="Your session has ended. Please log in again.",
                status_code=401,
            )

        user = await self._repo.get_by_id(row.user_id)
        if user is None:
            await self._refresh_tokens.revoke(
                row,
                reason="user_not_found",
                revoked_at=now,
            )
            log.warning(
                "auth_refresh_failed",
                observability_event="auth_refresh_failed",
                reason="user_not_found",
                user_id=str(row.user_id),
                client_ip=client_ip,
            )
            raise AppError(
                code="user_not_found",
                message="We couldn't find your account.",
                status_code=401,
                message_key="errors.user_not_found",
            )

        session, next_row = await self._issue_session_tokens(
            user=user,
            client_ip=client_ip,
            user_agent=user_agent,
            family_id=row.family_id,
        )
        await self._refresh_tokens.revoke(
            row,
            reason="refresh_rotated",
            revoked_at=now,
            replaced_by_token_id=next_row.id,
        )
        return session
