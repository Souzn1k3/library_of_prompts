from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

_DEFAULT_JWT_PLACEHOLDER = "change-me-in-production-use-openssl-rand"
_PRIMARY_DATABASE_NAME = "prompts_vault"
_TEST_DATABASE_NAME = "prompts_vault_test"
_CANONICAL_DOCKER_DB_HOST = "db"
_CANONICAL_DOCKER_DB_PORT = 5432
_CANONICAL_SCHEMA = "public"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Prompts Vault API"
    app_env: Literal["docker", "local", "test", "validation"] = "local"
    canonical_compose_project: str = "website"
    debug: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/prompts_vault",
        description="Async SQLAlchemy URL",
    )
    expected_database_name: str | None = None
    expected_database_schema: str = _CANONICAL_SCHEMA
    expected_database_host: str | None = None
    expected_database_port: int | None = None
    startup_db_validation_enabled: bool = True
    duplicate_db_detection_enabled: bool = True
    duplicate_db_probe_hosts: str = "host.docker.internal,gateway.docker.internal,localhost,127.0.0.1"
    duplicate_db_probe_ports: str = "5432,55432"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cache_enabled: bool = True
    cache_default_ttl_seconds: int = 120
    redis_url: str | None = None
    slow_request_threshold_ms: int = 700
    economy_kpi_job_enabled: bool = True
    economy_kpi_job_interval_minutes: int = 60
    economy_kpi_job_lookback_days: int = 35
    telegram_bot_api_key: str | None = None
    legacy_bot_database_url: str | None = None

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

    @property
    def parsed_database_url(self) -> URL:
        try:
            return make_url(self.database_url)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL.") from exc

    @property
    def duplicate_db_probe_host_list(self) -> list[str]:
        return [host.strip().lower() for host in self.duplicate_db_probe_hosts.split(",") if host.strip()]

    @property
    def duplicate_db_probe_port_list(self) -> list[int]:
        ports: list[int] = []
        for raw_port in self.duplicate_db_probe_ports.split(","):
            value = raw_port.strip()
            if not value:
                continue
            try:
                port = int(value)
            except ValueError as exc:
                raise ValueError("DUPLICATE_DB_PROBE_PORTS must contain integers only.") from exc
            if port <= 0:
                raise ValueError("DUPLICATE_DB_PROBE_PORTS must contain positive integers only.")
            ports.append(port)
        return ports

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if not self.expected_database_name:
            self.expected_database_name = _TEST_DATABASE_NAME if self.app_env == "test" else _PRIMARY_DATABASE_NAME
        if not self.expected_database_host:
            if self.app_env == "docker":
                self.expected_database_host = _CANONICAL_DOCKER_DB_HOST
            elif self.app_env == "test":
                self.expected_database_host = "127.0.0.1"
            else:
                self.expected_database_host = "localhost"
        if not self.expected_database_port:
            self.expected_database_port = _CANONICAL_DOCKER_DB_PORT

        if not self.expected_database_schema.strip():
            raise ValueError("EXPECTED_DATABASE_SCHEMA must not be empty.")
        if not self.canonical_compose_project.strip():
            raise ValueError("CANONICAL_COMPOSE_PROJECT must not be empty.")
        if self.economy_kpi_job_interval_minutes <= 0:
            raise ValueError("ECONOMY_KPI_JOB_INTERVAL_MINUTES must be greater than 0.")
        if self.economy_kpi_job_lookback_days <= 0:
            raise ValueError("ECONOMY_KPI_JOB_LOOKBACK_DAYS must be greater than 0.")

        url = self.parsed_database_url
        driver = url.drivername.lower()
        host = (url.host or "").lower()
        port = url.port
        database_name = url.database or ""

        _ = self.duplicate_db_probe_port_list

        if self.app_env == "validation":
            if not (driver.startswith("postgresql+asyncpg") or driver.startswith("sqlite")):
                raise ValueError("APP_ENV=validation requires DATABASE_URL to use postgresql+asyncpg or sqlite.")
            return self

        if not driver.startswith("postgresql+asyncpg"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg outside validation mode.")
        if not database_name:
            raise ValueError("DATABASE_URL must include a database name.")
        if port is None:
            raise ValueError("DATABASE_URL must include an explicit port.")

        expected_host = (self.expected_database_host or "").lower()
        expected_port = int(self.expected_database_port)
        expected_database_name = self.expected_database_name or ""

        if self.app_env == "docker":
            if host != expected_host or expected_host != _CANONICAL_DOCKER_DB_HOST:
                raise ValueError(
                    "APP_ENV=docker requires DATABASE_URL to target the canonical db service host "
                    f"'{_CANONICAL_DOCKER_DB_HOST}'."
                )
            if port != expected_port or expected_port != _CANONICAL_DOCKER_DB_PORT:
                raise ValueError(
                    f"APP_ENV=docker requires DATABASE_URL to use port {_CANONICAL_DOCKER_DB_PORT}."
                )
            if database_name != expected_database_name or expected_database_name != _PRIMARY_DATABASE_NAME:
                raise ValueError(
                    f"APP_ENV=docker requires DATABASE_URL to target database '{_PRIMARY_DATABASE_NAME}'."
                )
            if host in {"localhost", "127.0.0.1", "host.docker.internal", "gateway.docker.internal"}:
                raise ValueError(
                    "APP_ENV=docker must connect to the internal db service only. Host fallback targets are forbidden."
                )
            return self

        allowed_hosts = {expected_host}
        if self.app_env in {"local", "test"}:
            if expected_host == "localhost":
                allowed_hosts.add("127.0.0.1")
            if expected_host == "127.0.0.1":
                allowed_hosts.add("localhost")
        if host not in allowed_hosts:
            raise ValueError(
                f"APP_ENV={self.app_env} requires DATABASE_URL host to match {sorted(allowed_hosts)}."
            )
        if port != expected_port:
            raise ValueError(
                f"APP_ENV={self.app_env} requires DATABASE_URL port to be {expected_port}."
            )
        if self.app_env == "local" and database_name != expected_database_name:
            raise ValueError(
                f"APP_ENV=local requires DATABASE_URL database name '{expected_database_name}'."
            )
        if self.app_env == "test":
            if database_name != expected_database_name:
                raise ValueError(
                    f"APP_ENV=test requires DATABASE_URL database name '{expected_database_name}'."
                )
            if database_name == _PRIMARY_DATABASE_NAME:
                raise ValueError("APP_ENV=test must not target the primary prompts_vault database.")
        return self

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
