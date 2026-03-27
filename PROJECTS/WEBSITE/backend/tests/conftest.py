"""Set environment before importing the application (session binds DB URL at import time)."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# In-process tests: skip Redis so cache/rate-limit stay in-memory.
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/prompts_vault",
)
os.environ.setdefault("JWT_SECRET_KEY", "pytest-test-jwt-secret-key-32chars-min!!")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("BILLING_MOCK_MODE", "true")
os.environ.setdefault("BILLING_CHECKOUT_SUCCESS_URL", "http://127.0.0.1:3000/dashboard?billing=success")
os.environ.setdefault("BILLING_CHECKOUT_CANCEL_URL", "http://127.0.0.1:3000/plans?billing=cancel")
os.environ.setdefault("BILLING_PORTAL_RETURN_URL", "http://127.0.0.1:3000/dashboard")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
os.environ.setdefault("CACHE_ENABLED", "true")


@pytest.fixture
def unique_email() -> str:
    return f"pytest_{uuid.uuid4().hex}@example.com"


@pytest_asyncio.fixture(autouse=True)
async def _reset_cache_and_rate_limiter() -> None:
    """Lifespan shutdown closes the global cache; clear singletons so the next test gets fresh backends."""
    yield
    import app.core.cache as cache_mod
    import app.core.rate_limit as rate_mod

    if cache_mod._cache is not None:
        try:
            await cache_mod._cache.close()
        except Exception:
            pass
        cache_mod._cache = None
    rate_mod._limiter = None


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
