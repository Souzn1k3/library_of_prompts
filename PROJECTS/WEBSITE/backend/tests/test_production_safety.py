"""Validate production-oriented settings and OpenAPI exposure."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    yield
    from app.config import get_settings

    get_settings.cache_clear()


def test_settings_reject_weak_jwt_when_debug_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "short")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        get_settings()


def test_settings_reject_insecure_cookies_when_debug_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-jwt-secret-key-min-32-chars-long!!")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_COOKIE_ALLOW_INSECURE", "false")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="AUTH_COOKIE_SECURE"):
        get_settings()


def test_openapi_disabled_when_debug_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-jwt-secret-key-min-32-chars-long!!")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    app = create_app()
    assert app.openapi_url is None
    assert app.docs_url is None
    assert app.redoc_url is None


def test_openapi_enabled_when_debug_true(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "pytest-test-jwt-secret-key-32chars-min!!")
    get_settings.cache_clear()
    app = create_app()
    assert app.openapi_url is not None
    assert app.docs_url is not None


def test_settings_reject_invalid_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("APP_ENV", "broken")
    monkeypatch.setenv("DEBUG", "true")
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        get_settings()


def test_settings_reject_docker_fallback_database_host(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("APP_ENV", "docker")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/prompts_vault")
    monkeypatch.setenv("EXPECTED_DATABASE_HOST", "db")
    monkeypatch.setenv("EXPECTED_DATABASE_PORT", "5432")
    monkeypatch.setenv("EXPECTED_DATABASE_NAME", "prompts_vault")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="canonical db service host"):
        get_settings()


def test_settings_reject_primary_database_for_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/prompts_vault")
    monkeypatch.setenv("EXPECTED_DATABASE_NAME", "prompts_vault")
    monkeypatch.setenv("EXPECTED_DATABASE_HOST", "127.0.0.1")
    monkeypatch.setenv("EXPECTED_DATABASE_PORT", "5432")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="must not target the primary prompts_vault database"):
        get_settings()


def test_runtime_guard_rejects_missing_store_wallet_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings
    from app.core.runtime_guard import DatabaseRuntimeState, validate_database_state

    monkeypatch.setenv("APP_ENV", "docker")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/prompts_vault")
    monkeypatch.setenv("EXPECTED_DATABASE_HOST", "db")
    monkeypatch.setenv("EXPECTED_DATABASE_PORT", "5432")
    monkeypatch.setenv("EXPECTED_DATABASE_NAME", "prompts_vault")
    get_settings.cache_clear()
    settings = get_settings()

    state = DatabaseRuntimeState(
        database_name="prompts_vault",
        schema_name="public",
        alembic_heads=("20260328_0013",),
        table_names=frozenset({"alembic_version", "users", "prompts", "lessons", "lesson_missions"}),
    )
    with pytest.raises(RuntimeError, match="store_items"):
        validate_database_state(settings, state, expected_heads=("20260328_0013",))


def test_runtime_guard_rejects_wrong_alembic_head(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings
    from app.core.runtime_guard import DatabaseRuntimeState, validate_database_state

    monkeypatch.setenv("APP_ENV", "docker")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/prompts_vault")
    monkeypatch.setenv("EXPECTED_DATABASE_HOST", "db")
    monkeypatch.setenv("EXPECTED_DATABASE_PORT", "5432")
    monkeypatch.setenv("EXPECTED_DATABASE_NAME", "prompts_vault")
    get_settings.cache_clear()
    settings = get_settings()

    state = DatabaseRuntimeState(
        database_name="prompts_vault",
        schema_name="public",
        alembic_heads=("20260327_0012",),
        table_names=frozenset(
            {
                "alembic_version",
                "users",
                "prompts",
                "lessons",
                "lesson_missions",
                "onboarding_profiles",
                "store_items",
                "user_currency_balances",
                "currency_transactions",
                "user_purchases",
            }
        ),
    )
    with pytest.raises(RuntimeError, match="Alembic revision mismatch"):
        validate_database_state(settings, state, expected_heads=("20260328_0013",))
