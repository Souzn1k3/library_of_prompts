"""Set environment before importing the application (session binds DB URL at import time)."""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
import pytest_asyncio
import psycopg2
from psycopg2 import sql
from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# In-process tests: skip Redis so cache/rate-limit stay in-memory.
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/prompts_vault_test",
)
os.environ.setdefault("EXPECTED_DATABASE_NAME", "prompts_vault_test")
os.environ.setdefault("EXPECTED_DATABASE_SCHEMA", "public")
os.environ.setdefault("EXPECTED_DATABASE_HOST", "127.0.0.1")
os.environ.setdefault("EXPECTED_DATABASE_PORT", "5432")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-test-jwt-secret-key-32chars-min!!")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("BILLING_MOCK_MODE", "true")
os.environ.setdefault("BILLING_CHECKOUT_SUCCESS_URL", "http://127.0.0.1:3000/dashboard?billing=success")
os.environ.setdefault("BILLING_CHECKOUT_CANCEL_URL", "http://127.0.0.1:3000/plans?billing=cancel")
os.environ.setdefault("BILLING_PORTAL_RETURN_URL", "http://127.0.0.1:3000/dashboard")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
os.environ.setdefault("CACHE_ENABLED", "true")
os.environ.setdefault("TELEGRAM_BOT_API_KEY", "pytest-telegram-bot-sync-key")
os.environ.setdefault("TELEGRAM_REWARD_SIGNING_SECRET", "pytest-telegram-reward-signing-secret")
os.environ.setdefault("SCENARIO_FREE_DEMO_RUN_CAP", "3")
os.environ.setdefault("SCENARIO_GUEST_IP_DAILY_PROMPT_CAP", "12")
os.environ.setdefault("SCENARIO_GUEST_FINGERPRINT_DAILY_PROMPT_CAP", "8")
os.environ.setdefault("SCENARIO_GUEST_IP_ROTATION_PROMPT_CAP", "6")
os.environ.setdefault("SCENARIO_GUEST_ANTI_ABUSE_WINDOW_HOURS", "24")
os.environ.setdefault("WEB_DEMO_GAME_DAILY_TOKEN_CAP", "24")
os.environ.setdefault("WEB_DEMO_GAME_CHALLENGE_COOLDOWN_MINUTES", "720")
os.environ.setdefault("WEB_DEMO_GAME_GUEST_IP_DAILY_TOKEN_CAP", "72")
os.environ.setdefault("WEB_DEMO_GAME_GUEST_FINGERPRINT_DAILY_TOKEN_CAP", "36")
os.environ.setdefault("WEB_DEMO_GAME_GUEST_FINGERPRINT_WINDOW_MINUTES", "10")
os.environ.setdefault("WEB_DEMO_GAME_GUEST_FINGERPRINT_WINDOW_EVENT_CAP", "6")
os.environ.setdefault("SCENARIO_RUN_BOOST_TOKEN_COST", "12")
os.environ.setdefault("SCENARIO_RUN_BOOST_BONUS_RUNS", "3")
os.environ.setdefault("SCENARIO_CREATOR_PUBLISH_REWARD_TOKENS", "20")
os.environ.setdefault("SCENARIO_CREATOR_FORK_REWARD_TOKENS", "5")
os.environ.setdefault("SCENARIO_CREATOR_LIKE_REWARD_TOKENS", "1")
os.environ.setdefault("GROWTH_DASHBOARD_DEFAULT_WINDOW_DAYS", "28")
os.environ.setdefault("GROWTH_FLAG_DASHBOARD_ROLLOUT_PERCENT", "100")
os.environ.setdefault("GROWTH_FLAG_CHAIN_RECOMMENDATIONS_ROLLOUT_PERCENT", "100")
os.environ.setdefault("GROWTH_FLAG_SHOWCASE_SHARE_ROLLOUT_PERCENT", "100")
os.environ.setdefault("GROWTH_EXPERIMENT_HOMEPAGE_ROLLOUT_PERCENT", "50")
os.environ.setdefault("GROWTH_EXPERIMENT_LANDING_ROLLOUT_PERCENT", "50")
os.environ.setdefault("GROWTH_EXPERIMENT_UPGRADE_ROLLOUT_PERCENT", "50")
os.environ.setdefault("GROWTH_EXPERIMENT_PAYWALL_ROLLOUT_PERCENT", "50")
os.environ.setdefault("GROWTH_EXPERIMENT_PRICING_ROLLOUT_PERCENT", "50")
os.environ.setdefault("SCENARIO_AUTONOMY_ENABLED", "true")
os.environ.setdefault("SCENARIO_AUTONOMY_SCHEDULER_ENABLED", "false")
os.environ.setdefault("SCENARIO_AUTONOMY_INTERVAL_MINUTES", "45")
os.environ.setdefault("SCENARIO_AUTONOMY_SIGNAL_WINDOW_DAYS", "30")
os.environ.setdefault("SCENARIO_AUTONOMY_MAX_NEW_SCENARIOS_PER_CYCLE", "3")
os.environ.setdefault("SCENARIO_AUTONOMY_MIN_IMPROVEMENT_PERCENT", "3")
os.environ.setdefault("SCENARIO_AUTONOMY_GUARDRAIL_MIN_RETENTION_PERCENT", "25")
os.environ.setdefault("SCENARIO_AUTONOMY_GUARDRAIL_MAX_CAC_USD", "150")
os.environ.setdefault("SCENARIO_AUTONOMY_GUARDRAIL_MIN_ROI_PERCENT", "-10")
os.environ.setdefault("SCENARIO_AUTONOMY_MARKETPLACE_PRUNE_THRESHOLD", "18")
os.environ.setdefault("ECONOMY_KPI_JOB_ENABLED", "false")


def _sync_database_url(async_url: str) -> str:
    return async_url.replace("+asyncpg", "")


def _database_name(sync_url: str) -> str:
    return urlsplit(sync_url).path.lstrip("/")


def _admin_database_url(sync_url: str) -> str:
    parsed = urlsplit(sync_url)
    return urlunsplit(parsed._replace(path="/postgres"))


def _ensure_test_database() -> None:
    sync_url = _sync_database_url(os.environ["DATABASE_URL"])
    db_name = _database_name(sync_url)
    if not db_name:
        raise RuntimeError("DATABASE_URL must include a database name for tests.")
    if db_name == "prompts_vault":
        raise RuntimeError("Tests must not run against the primary prompts_vault database.")

    admin_url = _admin_database_url(sync_url)
    admin_conn = psycopg2.connect(admin_url)
    try:
        admin_conn.autocommit = True
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    finally:
        admin_conn.close()


def _reset_test_schema() -> None:
    sync_url = _sync_database_url(os.environ["DATABASE_URL"])
    with psycopg2.connect(sync_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cur.execute("CREATE SCHEMA public")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database() -> None:
    _ensure_test_database()
    _reset_test_schema()

    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"alembic upgrade head failed for test database: {details}")


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
