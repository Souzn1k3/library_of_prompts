import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.infrastructure.db.models import AuthRefreshToken, User, UserRole
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, SessionTokens
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository

log = get_logger(__name__)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_refresh_token_pair() -> tuple[str, str]:
    token_jti = uuid.uuid4().hex
    token = f"{token_jti}.{secrets.token_urlsafe(48)}"
    return token_jti, token


class AuthService:
    def __init__(
        self,
        repo: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        settings: Settings,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._refresh_tokens = refresh_tokens
        self._settings = settings
        self._analytics = analytics

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
        token_jti, refresh_token = _new_refresh_token_pair()
        refresh_row = AuthRefreshToken(
            user_id=user.id,
            token_hash=_hash_refresh_token(refresh_token),
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

    async def register(
        self,
        data: RegisterRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
    ) -> SessionTokens:
        email = data.email.lower()
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise ConflictError(
                "Email already registered",
                message_key="errors.email_already_registered",
            )

        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hash_password(data.password),
            display_name=data.display_name.strip(),
            role=UserRole.user,
        )
        created = await self._repo.create(user)
        if self._analytics is not None:
            domain = created.email.split("@", 1)[1] if "@" in created.email else None
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.signup_completed,
                user_id=created.id,
                metadata={
                    "user_role": created.role.value,
                    "plan_tier": created.plan_tier.value,
                    "email_domain": domain,
                },
                context_page="/api/v1/auth/register",
                context_feature="signup",
                event_id=f"signup_completed:{created.id}",
            )

        session, _ = await self._issue_session_tokens(
            user=created,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return session

    async def login(
        self,
        data: LoginRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
    ) -> SessionTokens:
        email = data.email.lower()
        user = await self._repo.get_by_email(email)
        if user is None or not verify_password(data.password, user.hashed_password):
            log.warning(
                "auth_login_failed",
                observability_event="auth_login_failed",
                email=email,
                reason="invalid_credentials",
                client_ip=client_ip,
            )
            raise AppError(
                code="invalid_credentials",
                message="Invalid email or password",
                status_code=401,
                message_key="errors.invalid_credentials",
            )
        session, _ = await self._issue_session_tokens(
            user=user,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return session

    async def refresh_session(
        self,
        *,
        refresh_token: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> SessionTokens:
        now = datetime.now(timezone.utc)
        row = await self._refresh_tokens.get_by_token_hash(_hash_refresh_token(refresh_token))
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

        expires_at = _as_utc(row.expires_at)
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

    async def logout(
        self,
        *,
        refresh_token: str | None,
        user_id: uuid.UUID | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        if refresh_token:
            row = await self._refresh_tokens.get_by_token_hash(_hash_refresh_token(refresh_token))
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
