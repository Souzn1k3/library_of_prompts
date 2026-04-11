from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from jose import JWTError, jwt

from app.config import Settings
from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger
from app.core.security import hash_password
from app.infrastructure.db.models import User, UserRole
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.identity.model.auth import SessionTokens
from app.modules.identity.repository.refresh_token_repository import RefreshTokenRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.auth_session_mixin import AuthSessionMixin

log = get_logger(__name__)

TelegramAuthMode = Literal["login", "link"]

TELEGRAM_OAUTH_BASE_URL = "https://oauth.telegram.org"
TELEGRAM_OAUTH_AUTHORIZE_URL = f"{TELEGRAM_OAUTH_BASE_URL}/auth"
TELEGRAM_OAUTH_TOKEN_URL = f"{TELEGRAM_OAUTH_BASE_URL}/token"
TELEGRAM_OAUTH_JWKS_URL = f"{TELEGRAM_OAUTH_BASE_URL}/auth/get_keys"
TELEGRAM_OAUTH_ISSUER = TELEGRAM_OAUTH_BASE_URL
TELEGRAM_SCOPE = "openid profile"
TELEGRAM_STATE_TOKEN_TYPE = "telegram_auth_state"


def _synthetic_email(telegram_user_id: int) -> str:
    return f"tg_{telegram_user_id}@telegram.local"


def _is_synthetic_email(email: str) -> bool:
    return email.lower().endswith("@telegram.local")


def _build_display_name(
    *,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    telegram_user_id: int,
) -> str:
    full_name = " ".join(part for part in (first_name, last_name) if part).strip()
    if full_name:
        return full_name[:120]
    if username:
        return username[:120]
    return f"Telegram User {telegram_user_id}"


def _coerce_telegram_user_id(payload: dict[str, Any]) -> int:
    raw = payload.get("id") or payload.get("sub")
    try:
        telegram_user_id = int(str(raw))
    except (TypeError, ValueError) as exc:
        raise AppError(
            code="telegram_auth_failed",
            message="Telegram did not return a valid user id.",
            status_code=401,
            message_key="errors.telegram_auth_failed",
        ) from exc
    if telegram_user_id <= 0:
        raise AppError(
            code="telegram_auth_failed",
            message="Telegram did not return a valid user id.",
            status_code=401,
            message_key="errors.telegram_auth_failed",
        )
    return telegram_user_id


def _safe_next_path(next_path: str | None, *, default_path: str) -> str:
    candidate = (next_path or "").strip()
    if not candidate:
        return default_path
    if not candidate.startswith("/") or candidate.startswith("//"):
        return default_path
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return default_path
    query = urlencode(parse_qsl(parsed.query, keep_blank_values=True))
    return urlunsplit(("", "", parsed.path, query, ""))


def _append_query_params(path: str, params: dict[str, str]) -> str:
    parsed = urlsplit(path)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value})
    return urlunsplit(("", "", parsed.path, urlencode(query), ""))


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


@dataclass(slots=True)
class TelegramOidcState:
    state: str
    code_verifier: str
    mode: TelegramAuthMode
    next_path: str
    link_user_id: uuid.UUID | None


@dataclass(slots=True)
class TelegramIdentity:
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language: str | None


@dataclass(slots=True)
class TelegramCallbackResult:
    user: User
    redirect_path: str
    session_tokens: SessionTokens | None
    linked: bool
    created: bool


class TelegramAuthService(AuthSessionMixin):
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

    def _require_configuration(self) -> None:
        if (
            not self._settings.telegram_login_client_id
            or not self._settings.telegram_login_client_secret
            or not self._settings.telegram_login_redirect_uri
        ):
            raise AppError(
                code="telegram_login_not_configured",
                message="Telegram login is not configured.",
                status_code=503,
                message_key="errors.telegram_login_not_configured",
            )

    def default_next_path(self, mode: TelegramAuthMode) -> str:
        return "/profile" if mode == "link" else "/dashboard"

    def create_state_token(
        self,
        *,
        mode: TelegramAuthMode,
        next_path: str | None,
        link_user_id: uuid.UUID | None,
    ) -> tuple[str, str]:
        self._require_configuration()
        state = secrets.token_urlsafe(24)
        code_verifier = secrets.token_urlsafe(64)
        payload = {
            "sub": "telegram-auth",
            "typ": TELEGRAM_STATE_TOKEN_TYPE,
            "jti": uuid.uuid4().hex,
            "state": state,
            "code_verifier": code_verifier,
            "mode": mode,
            "next_path": _safe_next_path(next_path, default_path=self.default_next_path(mode)),
            "link_user_id": str(link_user_id) if link_user_id is not None else None,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = jwt.encode(payload, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm)
        return state, token

    def decode_state_token(self, token: str) -> TelegramOidcState:
        try:
            payload = jwt.decode(token, self._settings.jwt_secret_key, algorithms=[self._settings.jwt_algorithm])
        except JWTError as exc:
            raise AppError(
                code="invalid_telegram_auth_state",
                message="Telegram sign-in session expired. Please try again.",
                status_code=401,
                message_key="errors.invalid_telegram_auth_state",
            ) from exc

        if payload.get("typ") != TELEGRAM_STATE_TOKEN_TYPE:
            raise AppError(
                code="invalid_telegram_auth_state",
                message="Telegram sign-in session expired. Please try again.",
                status_code=401,
                message_key="errors.invalid_telegram_auth_state",
            )

        mode = str(payload.get("mode") or "login")
        if mode not in {"login", "link"}:
            raise AppError(
                code="invalid_telegram_auth_state",
                message="Telegram sign-in session expired. Please try again.",
                status_code=401,
                message_key="errors.invalid_telegram_auth_state",
            )

        link_user_id: uuid.UUID | None = None
        raw_link_user_id = payload.get("link_user_id")
        if raw_link_user_id:
            try:
                link_user_id = uuid.UUID(str(raw_link_user_id))
            except ValueError as exc:
                raise AppError(
                    code="invalid_telegram_auth_state",
                    message="Telegram sign-in session expired. Please try again.",
                    status_code=401,
                    message_key="errors.invalid_telegram_auth_state",
                ) from exc

        return TelegramOidcState(
            state=str(payload.get("state") or ""),
            code_verifier=str(payload.get("code_verifier") or ""),
            mode=mode,
            next_path=_safe_next_path(
                str(payload.get("next_path") or ""),
                default_path=self.default_next_path(mode),
            ),
            link_user_id=link_user_id,
        )

    def build_authorization_url(self, *, state: str, state_token: str) -> str:
        self._require_configuration()
        parsed_state = self.decode_state_token(state_token)
        query = urlencode(
            {
                "client_id": self._settings.telegram_login_client_id or "",
                "redirect_uri": self._settings.telegram_login_redirect_uri or "",
                "response_type": "code",
                "scope": TELEGRAM_SCOPE,
                "state": state,
                "code_challenge": _pkce_challenge(parsed_state.code_verifier),
                "code_challenge_method": "S256",
            }
        )
        return f"{TELEGRAM_OAUTH_AUTHORIZE_URL}?{query}"

    def callback_failure_path(
        self,
        *,
        mode: TelegramAuthMode,
        next_path: str | None = None,
        reason: str,
    ) -> str:
        fallback = self.default_next_path(mode)
        target = _safe_next_path(next_path, default_path=fallback)
        if mode == "link":
            return _append_query_params(target, {"telegram_error": reason})
        return _append_query_params("/login", {"telegram_error": reason})

    async def complete_authorization(
        self,
        *,
        code: str,
        returned_state: str,
        state_token: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> TelegramCallbackResult:
        self._require_configuration()
        auth_state = self.decode_state_token(state_token)
        if not auth_state.state or auth_state.state != returned_state:
            raise AppError(
                code="invalid_telegram_auth_state",
                message="Telegram sign-in session expired. Please try again.",
                status_code=401,
                message_key="errors.invalid_telegram_auth_state",
            )

        token_payload = await self._exchange_code_for_tokens(
            code=code,
            code_verifier=auth_state.code_verifier,
        )
        telegram_claims = await self._verify_id_token(token_payload["id_token"])
        identity = self._identity_from_claims(telegram_claims)

        if auth_state.mode == "link":
            linked_user = await self._link_identity(
                link_user_id=auth_state.link_user_id,
                identity=identity,
            )
            return TelegramCallbackResult(
                user=linked_user,
                redirect_path=_append_query_params(auth_state.next_path, {"telegram": "linked"}),
                session_tokens=None,
                linked=True,
                created=False,
            )

        authed_user, created = await self._login_or_register(identity)
        session_tokens, _ = await self._issue_session_tokens(
            user=authed_user,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return TelegramCallbackResult(
            user=authed_user,
            redirect_path=auth_state.next_path,
            session_tokens=session_tokens,
            linked=authed_user.telegram_user_id is not None,
            created=created,
        )

    async def _login_or_register(self, identity: TelegramIdentity) -> tuple[User, bool]:
        user = await self._repo.get_by_telegram_user_id(identity.telegram_user_id)
        if user is None:
            user = await self._repo.get_by_email(_synthetic_email(identity.telegram_user_id))

        if user is None:
            user = User(
                email=_synthetic_email(identity.telegram_user_id),
                hashed_password=hash_password(secrets.token_urlsafe(24)),
                display_name=_build_display_name(
                    username=identity.username,
                    first_name=identity.first_name,
                    last_name=identity.last_name,
                    telegram_user_id=identity.telegram_user_id,
                ),
                role=UserRole.user,
                telegram_user_id=identity.telegram_user_id,
                telegram_username=identity.username,
                telegram_first_name=identity.first_name,
                telegram_last_name=identity.last_name,
                telegram_language=identity.language,
            )
            created = await self._repo.create(user)
            await self._record_signup_completed(created)
            return created, True

        updated = await self._apply_identity(user, identity)
        return updated, False

    async def _link_identity(self, *, link_user_id: uuid.UUID | None, identity: TelegramIdentity) -> User:
        if link_user_id is None:
            raise AppError(
                code="not_authenticated",
                message="Please log in before linking Telegram.",
                status_code=401,
                message_key="errors.invalid_or_expired_token",
            )

        user = await self._repo.get_by_id(link_user_id)
        if user is None:
            raise AppError(
                code="user_not_found",
                message="We couldn't find your account.",
                status_code=401,
                message_key="errors.user_not_found",
            )

        if user.telegram_user_id is not None and user.telegram_user_id != identity.telegram_user_id:
            raise ConflictError(
                "This account is already linked to another Telegram user.",
                message_key="errors.telegram_account_mismatch",
            )

        existing_owner = await self._repo.get_by_telegram_user_id(identity.telegram_user_id)
        if existing_owner is not None and existing_owner.id != user.id:
            raise ConflictError(
                "Telegram account is already linked to another site account.",
                message_key="errors.telegram_already_linked",
            )

        return await self._apply_identity(user, identity)

    async def _apply_identity(self, user: User, identity: TelegramIdentity) -> User:
        user.telegram_user_id = identity.telegram_user_id
        if identity.username is not None:
            user.telegram_username = identity.username
        if identity.first_name is not None:
            user.telegram_first_name = identity.first_name
        if identity.last_name is not None:
            user.telegram_last_name = identity.last_name
        if identity.language is not None:
            user.telegram_language = identity.language[:10]
        if _is_synthetic_email(user.email):
            user.display_name = _build_display_name(
                username=identity.username,
                first_name=identity.first_name,
                last_name=identity.last_name,
                telegram_user_id=identity.telegram_user_id,
            )
        return await self._repo.save(user)

    def _identity_from_claims(self, claims: dict[str, Any]) -> TelegramIdentity:
        username = claims.get("username") or claims.get("preferred_username")
        first_name = claims.get("first_name") or claims.get("given_name")
        last_name = claims.get("last_name") or claims.get("family_name")
        language = claims.get("language_code") or claims.get("locale")
        return TelegramIdentity(
            telegram_user_id=_coerce_telegram_user_id(claims),
            username=str(username)[:255] if username else None,
            first_name=str(first_name)[:255] if first_name else None,
            last_name=str(last_name)[:255] if last_name else None,
            language=str(language)[:10] if language else None,
        )

    async def _exchange_code_for_tokens(self, *, code: str, code_verifier: str) -> dict[str, Any]:
        auth_bytes = (
            f"{self._settings.telegram_login_client_id}:{self._settings.telegram_login_client_secret}".encode("utf-8")
        )
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.telegram_login_redirect_uri or "",
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(TELEGRAM_OAUTH_TOKEN_URL, data=data, headers=headers)

        if response.status_code >= 400:
            log.warning(
                "telegram_token_exchange_failed",
                observability_event="telegram_token_exchange_failed",
                status_code=response.status_code,
                response_body=response.text[:400],
            )
            raise AppError(
                code="telegram_auth_failed",
                message="Telegram login could not be verified.",
                status_code=401,
                message_key="errors.telegram_auth_failed",
            )

        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("id_token"):
            raise AppError(
                code="telegram_auth_failed",
                message="Telegram login could not be verified.",
                status_code=401,
                message_key="errors.telegram_auth_failed",
            )
        return payload

    async def _verify_id_token(self, id_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            jwks_response = await client.get(TELEGRAM_OAUTH_JWKS_URL, headers={"Accept": "application/json"})

        if jwks_response.status_code >= 400:
            log.warning(
                "telegram_jwks_fetch_failed",
                observability_event="telegram_jwks_fetch_failed",
                status_code=jwks_response.status_code,
                response_body=jwks_response.text[:400],
            )
            raise AppError(
                code="telegram_auth_failed",
                message="Telegram login could not be verified.",
                status_code=401,
                message_key="errors.telegram_auth_failed",
            )

        jwks_payload = jwks_response.json()
        if not isinstance(jwks_payload, dict):
            raise AppError(
                code="telegram_auth_failed",
                message="Telegram login could not be verified.",
                status_code=401,
                message_key="errors.telegram_auth_failed",
            )

        header = jwt.get_unverified_header(id_token)
        algorithm = str(header.get("alg") or "RS256")
        try:
            return jwt.decode(
                id_token,
                jwks_payload,
                algorithms=[algorithm],
                audience=self._settings.telegram_login_client_id,
                issuer=TELEGRAM_OAUTH_ISSUER,
                options={"require_exp": True, "require_aud": True, "require_iss": True},
            )
        except JWTError as exc:
            raise AppError(
                code="telegram_auth_failed",
                message="Telegram login could not be verified.",
                status_code=401,
                message_key="errors.telegram_auth_failed",
            ) from exc

    async def _record_signup_completed(self, user: User) -> None:
        if self._analytics is None:
            return
        domain = user.email.split("@", 1)[1] if "@" in user.email else None
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.signup_completed,
            user_id=user.id,
            metadata={
                "user_role": user.role.value,
                "plan_tier": user.plan_tier.value,
                "email_domain": domain,
                "auth_provider": "telegram",
            },
            context_page="/api/v1/auth/telegram/callback",
            context_feature="telegram_auth",
            event_id=f"signup_completed:telegram:{user.id}",
        )
