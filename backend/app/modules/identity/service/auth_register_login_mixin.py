from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.infrastructure.db.models import User, UserRole
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.identity.model.auth import LoginRequest, RegisterRequest, SessionTokens

log = get_logger(__name__)


class AuthRegisterLoginMixin:
    async def register(
        self,
        data: RegisterRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
    ) -> SessionTokens:
        email = data.email.lower()
        display_name = self._display_names.normalize_required(data.display_name)
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise ConflictError(
                "Email already registered",
                message_key="errors.email_already_registered",
            )
        await self._display_names.ensure_available(self._repo, display_name)

        user = User(
            email=email,
            hashed_password=hash_password(data.password),
            display_name=display_name,
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
