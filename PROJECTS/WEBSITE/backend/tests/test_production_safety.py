"""Validate production-oriented settings and OpenAPI exposure."""

from __future__ import annotations

import pytest


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
