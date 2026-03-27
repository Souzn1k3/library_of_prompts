from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_PLACEHOLDER = "change-me-in-production-use-openssl-rand"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Prompts Vault API"
    debug: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/prompts_vault",
        description="Async SQLAlchemy URL",
    )
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cache_enabled: bool = True
    cache_default_ttl_seconds: int = 120
    redis_url: str | None = None
    slow_request_threshold_ms: int = 700

    jwt_secret_key: str = Field(
        default=_DEFAULT_JWT_PLACEHOLDER,
        description="HS256 signing key for access tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    access_token_cookie_name: str = "pv_access_token"
    refresh_token_cookie_name: str = "pv_refresh_token"
    auth_cookie_domain: str | None = None
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    # Local HTTP only: allows cookies without Secure when DEBUG=false
    auth_cookie_allow_insecure: bool = False
    # Set only behind a trusted reverse proxy (rate-limit client IP from X-Forwarded-For)
    rate_limit_trust_forwarded_for: bool = False
    legacy_bearer_auth_enabled: bool = True

    # Billing
    billing_mock_mode: bool = False
    billing_checkout_success_url: str = "http://localhost:3000/dashboard?billing=success"
    billing_checkout_cancel_url: str = "http://localhost:3000/plans?billing=cancel"
    billing_portal_return_url: str = "http://localhost:3000/dashboard"

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_starter: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_enterprise: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.debug:
            return self
        if self.jwt_secret_key == _DEFAULT_JWT_PLACEHOLDER or len(self.jwt_secret_key) < 32:
            raise ValueError(
                "When DEBUG=false, JWT_SECRET_KEY must be set to a random value of at least 32 characters."
            )
        if not self.auth_cookie_secure and not self.auth_cookie_allow_insecure:
            raise ValueError(
                "When DEBUG=false, set AUTH_COOKIE_SECURE=true for HTTPS deployments, "
                "or AUTH_COOKIE_ALLOW_INSECURE=true only for local HTTP development."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
