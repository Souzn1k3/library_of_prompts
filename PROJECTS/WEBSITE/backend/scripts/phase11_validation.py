from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit

# Configure env before importing app modules.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _database_name(database_url: str) -> str:
    return urlsplit(database_url.replace("+asyncpg", "")).path.lstrip("/")


VALIDATION_MODE = (os.getenv("PHASE11_VALIDATION_MODE") or "local").strip().lower()
if VALIDATION_MODE not in {"local", "real"}:
    raise RuntimeError("PHASE11_VALIDATION_MODE must be either 'local' or 'real'")

REQUIRE_STRIPE_WEBHOOK = _env_flag(
    "PHASE11_REQUIRE_STRIPE_WEBHOOK",
    default=VALIDATION_MODE == "real",
)
ALLOW_PRIMARY_DB_RESET = _env_flag("PHASE11_ALLOW_PRIMARY_DB_RESET", default=False)

if VALIDATION_MODE == "local":
    db_path = PROJECT_ROOT / "phase11_validation.db"
    if db_path.exists():
        db_path.unlink()
    os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    os.environ.setdefault("BILLING_MOCK_MODE", "true")
else:
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/prompts_vault_phase11",
    )
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("BILLING_MOCK_MODE", "false")

    if _database_name(os.environ["DATABASE_URL"]) == "prompts_vault" and not ALLOW_PRIMARY_DB_RESET:
        raise RuntimeError(
            "PHASE11 real mode refuses to use the primary prompts_vault database. "
            "Point DATABASE_URL to a dedicated validation database or set "
            "PHASE11_ALLOW_PRIMARY_DB_RESET=true to override intentionally."
        )

os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("APP_ENV", "validation")
os.environ.setdefault("CACHE_ENABLED", "true")
os.environ.setdefault("JWT_SECRET_KEY", "phase11-validation-secret-key-min-32chars!!")
os.environ.setdefault("AUTH_COOKIE_ALLOW_INSECURE", "true")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ.setdefault("LEGACY_BEARER_AUTH_ENABLED", "true")

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, inspect, select, text, update

from app.config import get_settings
from app.core.cache import get_cache
from app.core.security import hash_password
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import (
    AnalyticsEvent,
    Category,
    ContributorProfile,
    ContributorTier,
    Lesson,
    LessonMission,
    LessonMissionPrompt,
    MissionActionType,
    ModelCompatibility,
    ModerationState,
    OnboardingGoal,
    OnboardingRole,
    Plan,
    PlanTier,
    Prompt,
    PromptDifficulty,
    PromptModelCompatibility,
    PromptOutputType,
    PromptQualityMetric,
    PromptStats,
    PromptStatus,
    PromptTag,
    PromptTechnique,
    PromptUseCase,
    Tag,
    UseCase,
    User,
    UserRole,
)
from app.infrastructure.db.session import async_session_maker, engine
from app.main import create_app
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.missions.repository.mission_repository import MissionRepository


@dataclass
class ValidationReport:
    checks: list[str] = field(default_factory=list)
    perf_ms: list[tuple[str, float]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def add_check(self, name: str) -> None:
        self.checks.append(name)

    def add_timing(self, name: str, elapsed_ms: float) -> None:
        self.perf_ms.append((name, elapsed_ms))

    def add_blocker(self, message: str) -> None:
        self.blockers.append(message)

    def slow_checks(self, threshold_ms: float = 700.0) -> list[tuple[str, float]]:
        return [row for row in self.perf_ms if row[1] >= threshold_ms]


@dataclass
class SeedState:
    category_public_id: uuid.UUID
    category_restricted_id: uuid.UUID
    free_prompt_id: uuid.UUID
    free_prompt_slug: str
    second_prompt_id: uuid.UUID
    premium_prompt_slug: str
    lesson_slug: str
    moderator_email: str
    moderator_password: str
    admin_email: str
    admin_password: str


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _stripe_checkout_configured() -> bool:
    settings = get_settings()
    return bool(settings.stripe_secret_key and settings.stripe_price_starter)


def _stripe_webhook_configured() -> bool:
    settings = get_settings()
    return bool(settings.stripe_secret_key and settings.stripe_webhook_secret)


def _build_stripe_signature_header(*, payload: bytes, secret: str, timestamp: int | None = None) -> str:
    ts = timestamp or int(datetime.now(timezone.utc).timestamp())
    signed_payload = f"{ts}.".encode("utf-8") + payload
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={signature}"


def _build_subscription_webhook_event(*, user_id: str) -> dict[str, Any]:
    now = int(datetime.now(timezone.utc).timestamp())
    period_end = now + 30 * 24 * 60 * 60
    settings = get_settings()
    starter_price_id = settings.stripe_price_starter or f"price_phase11_{uuid.uuid4().hex[:10]}"

    return {
        "id": f"evt_phase11_{uuid.uuid4().hex[:18]}",
        "type": "customer.subscription.updated",
        "created": now,
        "data": {
            "object": {
                "id": f"sub_phase11_{uuid.uuid4().hex[:18]}",
                "customer": f"cus_phase11_{uuid.uuid4().hex[:18]}",
                "status": "active",
                "current_period_start": now,
                "current_period_end": period_end,
                "trial_end": None,
                "cancel_at_period_end": False,
                "canceled_at": None,
                "metadata": {
                    "tier": "starter",
                    "user_id": user_id,
                },
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": starter_price_id,
                            }
                        }
                    ]
                },
            }
        },
    }


async def _api(
    report: ValidationReport,
    client: AsyncClient,
    method: str,
    path: str,
    expected_status: int,
    *,
    label: str,
    **kwargs: Any,
):
    started = perf_counter()
    response = await client.request(method, path, **kwargs)
    elapsed_ms = (perf_counter() - started) * 1000
    report.add_timing(label, elapsed_ms)
    _ensure(
        response.status_code == expected_status,
        f"{label}: expected {expected_status}, got {response.status_code}, body={response.text}",
    )
    report.add_check(label)
    return response


async def _reset_schema() -> None:
    if VALIDATION_MODE == "real" and engine.dialect.name == "postgresql":
        async with engine.begin() as conn:
            await conn.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
            await conn.exec_driver_sql("CREATE SCHEMA public")
            await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        result = await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"alembic upgrade head failed: {details}")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        if engine.dialect.name == "postgresql":
            await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        await conn.run_sync(Base.metadata.create_all)


async def _seed_data() -> SeedState:
    moderator_password = "ModeratorPass123!"
    admin_password = "AdminPass123!"

    async with async_session_maker() as session:
        if VALIDATION_MODE == "real" and engine.dialect.name == "postgresql":
            # Migrations seed baseline catalog/billing rows. Clear them so this validator has deterministic fixtures.
            await session.execute(delete(Plan))
            await session.execute(delete(UseCase))
            await session.execute(delete(ModelCompatibility))
            await session.execute(delete(Tag))

        free = Plan(
            tier=PlanTier.free,
            name="Free",
            description="Free tier",
            price_usd_month=0,
            is_active=True,
            sort_order=0,
        )
        starter = Plan(
            tier=PlanTier.starter,
            name="Starter",
            description="Starter tier",
            price_usd_month=15,
            is_active=True,
            sort_order=1,
        )
        pro = Plan(
            tier=PlanTier.pro,
            name="Pro",
            description="Pro tier",
            price_usd_month=39,
            is_active=True,
            sort_order=2,
        )
        enterprise = Plan(
            tier=PlanTier.enterprise,
            name="Enterprise",
            description="Enterprise tier",
            price_usd_month=99,
            is_active=True,
            sort_order=3,
        )
        session.add_all([free, starter, pro, enterprise])

        category_public = Category(slug="development", name="Development", sort_order=1, is_restricted=False)
        category_restricted = Category(
            slug="enterprise", name="Enterprise Workflows", sort_order=2, is_restricted=True
        )
        session.add_all([category_public, category_restricted])

        use_case_debug = UseCase(slug="debugging", name="Debugging", sort_order=1)
        use_case_study = UseCase(slug="studying", name="Studying", sort_order=2)
        model_gpt4o = ModelCompatibility(slug="gpt-4o-mini", name="GPT-4o mini", sort_order=1)
        model_claude = ModelCompatibility(slug="claude-3-7", name="Claude 3.7", sort_order=2)
        tag_react = Tag(slug="react", name="React")
        tag_api = Tag(slug="api", name="API")
        session.add_all([use_case_debug, use_case_study, model_gpt4o, model_claude, tag_react, tag_api])

        author = User(
            email="validation.curated@promptsvault.local",
            hashed_password=hash_password("ValidationCuratorPass123!"),
            display_name="Prompts Vault Curated",
            role=UserRole.user,
        )
        moderator = User(
            email="moderator@promptsvault.com",
            hashed_password=hash_password(moderator_password),
            display_name="Moderator",
            role=UserRole.moderator,
        )
        admin = User(
            email="admin@promptsvault.com",
            hashed_password=hash_password(admin_password),
            display_name="Admin",
            role=UserRole.admin,
        )
        session.add_all([author, moderator, admin])
        await session.flush()

        author_profile = ContributorProfile(
            user_id=author.id,
            slug="validation-curated",
            reputation_score=72,
            reputation_tier=ContributorTier.verified,
            total_submissions=3,
            approved_submissions=3,
            rejected_submissions=0,
            rejection_rate=0,
            total_saves=32,
            total_copies=44,
            mission_success_count=12,
            average_prompt_quality=76,
            computed_at=datetime.now(timezone.utc),
        )
        session.add(author_profile)

        lesson = Lesson(
            slug="prompt-basics",
            title="Prompt Basics",
            body=(
                "Learn how to turn vague asks into actionable prompts with explicit context, "
                "constraints, and output formatting."
            ),
            min_tier=PlanTier.free,
            sort_order=1,
        )
        lesson_pro = Lesson(
            slug="advanced-evaluation",
            title="Advanced Prompt Evaluation",
            body="How to evaluate prompt quality with scoring rubrics and failure-mode tests.",
            min_tier=PlanTier.pro,
            sort_order=2,
        )
        session.add_all([lesson, lesson_pro])
        await session.flush()

        free_prompt = Prompt(
            slug="react-debug-checklist",
            title="React Debug Checklist",
            body=(
                "You are a senior React debugger. Diagnose this bug with a step-by-step checklist, "
                "state assumptions, and propose the smallest safe fix first."
            ),
            summary="Find React bugs quickly with a structured diagnosis flow.",
            status=PromptStatus.published,
            technique=PromptTechnique.few_shot,
            difficulty=PromptDifficulty.beginner,
            output_type=PromptOutputType.code,
            category_id=category_public.id,
            author_id=author.id,
            moderation_state=ModerationState.approved,
            is_premium=False,
        )
        second_prompt = Prompt(
            slug="study-topic-explainer",
            title="Study Topic Explainer",
            body=(
                "Explain this topic for a student at my level. Include key ideas, common mistakes, "
                "and three practice questions with answers."
            ),
            summary="Convert complex topics into student-friendly lessons.",
            status=PromptStatus.published,
            technique=PromptTechnique.zero_shot,
            difficulty=PromptDifficulty.beginner,
            output_type=PromptOutputType.text,
            category_id=category_public.id,
            author_id=author.id,
            moderation_state=ModerationState.approved,
            is_premium=False,
        )
        premium_prompt = Prompt(
            slug="enterprise-code-reviewer",
            title="Enterprise Code Reviewer",
            body=(
                "Perform an enterprise-grade code review with architecture, security, and compliance "
                "risks prioritized. Provide severity and remediation plans."
            ),
            summary="Deep review template for high-stakes code changes.",
            status=PromptStatus.published,
            technique=PromptTechnique.chain_of_thought,
            difficulty=PromptDifficulty.advanced,
            output_type=PromptOutputType.structured,
            category_id=category_public.id,
            author_id=author.id,
            moderation_state=ModerationState.approved,
            is_premium=True,
        )
        session.add_all([free_prompt, second_prompt, premium_prompt])
        await session.flush()

        session.add_all(
            [
                PromptStats(
                    prompt_id=free_prompt.id,
                    save_count=8,
                    copy_count=19,
                    view_count=44,
                    quality_score=78,
                ),
                PromptStats(
                    prompt_id=second_prompt.id,
                    save_count=5,
                    copy_count=10,
                    view_count=31,
                    quality_score=70,
                ),
                PromptStats(
                    prompt_id=premium_prompt.id,
                    save_count=3,
                    copy_count=6,
                    view_count=20,
                    quality_score=82,
                ),
                PromptQualityMetric(
                    prompt_id=free_prompt.id,
                    unique_savers=8,
                    copy_events=19,
                    mission_success_events=4,
                    quality_score=83,
                    computed_at=datetime.now(timezone.utc),
                ),
                PromptQualityMetric(
                    prompt_id=second_prompt.id,
                    unique_savers=5,
                    copy_events=10,
                    mission_success_events=2,
                    quality_score=68,
                    computed_at=datetime.now(timezone.utc),
                ),
                PromptUseCase(prompt_id=free_prompt.id, use_case_id=use_case_debug.id),
                PromptUseCase(prompt_id=second_prompt.id, use_case_id=use_case_study.id),
                PromptModelCompatibility(prompt_id=free_prompt.id, model_id=model_gpt4o.id),
                PromptModelCompatibility(prompt_id=second_prompt.id, model_id=model_claude.id),
                PromptTag(prompt_id=free_prompt.id, tag_id=tag_react.id),
                PromptTag(prompt_id=free_prompt.id, tag_id=tag_api.id),
                PromptTag(prompt_id=second_prompt.id, tag_id=tag_api.id),
            ]
        )

        onboarding_mission = LessonMission(
            slug="first-win",
            title="Complete your first win",
            description="Finish onboarding and execute your first useful prompt.",
            objective="Get a first successful prompt outcome",
            completion_condition="Complete onboarding first win action once",
            action_type=MissionActionType.onboarding_first_win,
            required_count=1,
            persona_role=OnboardingRole.student,
            persona_goal=OnboardingGoal.learning,
            lesson_id=lesson.id,
            reward_badge="first_win",
            reward_credits=5,
            reward_premium_days=0,
            is_active=True,
            sort_order=1,
        )
        save_mission = LessonMission(
            slug="save-a-prompt",
            title="Save a prompt to your vault",
            description="Practice using discovery and save a useful prompt.",
            objective="Save one relevant prompt",
            completion_condition="Save at least 1 linked prompt",
            action_type=MissionActionType.copy_or_save_prompt,
            required_count=1,
            persona_role=OnboardingRole.student,
            persona_goal=OnboardingGoal.learning,
            lesson_id=lesson.id,
            reward_badge="prompt_saver",
            reward_credits=10,
            reward_premium_days=0,
            is_active=True,
            sort_order=2,
        )
        lesson_mission = LessonMission(
            slug="complete-basics-lesson",
            title="Complete Prompt Basics lesson",
            description="Finish lesson and apply one practical idea.",
            objective="Finish the basics lesson",
            completion_condition="Mark linked lesson complete",
            action_type=MissionActionType.lesson_completed,
            required_count=1,
            persona_role=OnboardingRole.student,
            persona_goal=OnboardingGoal.learning,
            lesson_id=lesson.id,
            reward_badge=None,
            reward_credits=0,
            reward_premium_days=0,
            is_active=True,
            sort_order=3,
        )
        session.add_all([onboarding_mission, save_mission, lesson_mission])
        await session.flush()

        session.add(
            LessonMissionPrompt(
                mission_id=save_mission.id,
                prompt_id=free_prompt.id,
                sort_order=1,
            )
        )

        await session.commit()

        return SeedState(
            category_public_id=category_public.id,
            category_restricted_id=category_restricted.id,
            free_prompt_id=free_prompt.id,
            free_prompt_slug=free_prompt.slug,
            second_prompt_id=second_prompt.id,
            premium_prompt_slug=premium_prompt.slug,
            lesson_slug=lesson.slug,
            moderator_email=moderator.email,
            moderator_password=moderator_password,
            admin_email=admin.email,
            admin_password=admin_password,
        )


async def _validate_runtime_configuration(report: ValidationReport) -> None:
    settings = get_settings()
    if VALIDATION_MODE == "real":
        _ensure(
            settings.database_url.startswith("postgresql+asyncpg://"),
            "real mode requires DATABASE_URL with postgresql+asyncpg",
        )
        _ensure("sqlite" not in settings.database_url.lower(), "real mode cannot use SQLite fallback")
        _ensure(bool(settings.redis_url), "real mode requires REDIS_URL")
        cache = get_cache()
        _ensure(getattr(cache, "_uses_redis", False), "real mode requires active Redis cache backend")
        report.add_check("runtime_postgres_configured")
        report.add_check("runtime_no_sqlite_fallback")
        report.add_check("runtime_redis_configured")
        report.add_check("runtime_redis_backend_active")
    else:
        _ensure(
            settings.database_url.startswith("sqlite+aiosqlite://"),
            "local mode requires sqlite+aiosqlite DATABASE_URL",
        )
        report.add_check("runtime_sqlite_configured")


async def _validate_runtime_dialect_paths(report: ValidationReport) -> None:
    if VALIDATION_MODE != "real":
        return
    async with async_session_maker() as session:
        analytics_repo = AnalyticsRepository(session)
        prompt_repo = PromptRepository(session)
        mission_repo = MissionRepository(session)
        contributor_repo = ContributorRepository(session)

        _ensure(not analytics_repo._is_sqlite(), "Analytics repository resolved SQLite path in real mode")
        _ensure(prompt_repo._is_postgresql(), "Prompt repository must use PostgreSQL search path in real mode")
        _ensure(not mission_repo._is_sqlite(), "Mission repository resolved SQLite path in real mode")

        contributor_insert_stmt = contributor_repo._insert(PromptQualityMetric)
        _ensure(
            "postgresql" in contributor_insert_stmt.__class__.__module__,
            "Contributor repository must use PostgreSQL INSERT dialect in real mode",
        )

    report.add_check("runtime_dialect_paths_postgresql")


async def _validate_schema(report: ValidationReport) -> None:
    expected_dialect = "postgresql" if VALIDATION_MODE == "real" else "sqlite"
    _ensure(
        engine.dialect.name == expected_dialect,
        f"Expected SQL dialect '{expected_dialect}', got '{engine.dialect.name}'",
    )
    report.add_check(f"db_dialect_{expected_dialect}")

    required_tables = {
        "plans",
        "subscriptions",
        "billing_customers",
        "subscription_events",
        "onboarding_profiles",
        "lesson_missions",
        "user_mission_progress",
        "mission_completion_events",
        "contributor_profiles",
        "prompt_quality_metrics",
        "analytics_events",
        "auth_refresh_tokens",
    }
    required_columns = {
        "onboarding_profiles": {"role", "goal", "ai_context", "first_win_completed_at"},
        "auth_refresh_tokens": {"token_hash", "family_id", "revoked_at", "replaced_by_token_id"},
        "analytics_events": {"event_id", "event_name", "session_id", "metadata_json"},
        "lesson_missions": {"action_type", "required_count", "reward_credits", "reward_premium_days"},
        "contributor_profiles": {"reputation_score", "reputation_tier", "approved_submissions"},
        "prompt_quality_metrics": {"quality_score", "mission_success_events"},
    }

    async with engine.begin() as conn:
        schema_info = await conn.run_sync(
            lambda sync_conn: (
                set(inspect(sync_conn).get_table_names()),
                {
                    table: {col["name"] for col in inspect(sync_conn).get_columns(table)}
                    for table in required_columns
                },
            )
        )

    table_names, table_columns = schema_info
    missing_tables = sorted(required_tables - table_names)
    _ensure(not missing_tables, f"Missing tables: {missing_tables}")

    for table, expected_columns in required_columns.items():
        present = table_columns.get(table, set())
        missing = sorted(expected_columns - present)
        _ensure(not missing, f"Table {table} missing columns: {missing}")

    if expected_dialect == "postgresql":
        required_indexes = {
            "ix_prompts_search_vector",
            "ix_prompts_title_trgm",
            "ix_prompts_summary_trgm",
            "ix_prompts_created_at",
            "ix_prompt_stats_save_count",
            "ix_prompt_stats_copy_count",
        }
        async with engine.begin() as conn:
            ext_present = (
                await conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm' LIMIT 1")
                )
            ).scalar_one_or_none()
            index_rows = (
                await conn.execute(
                    text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
                )
            ).scalars().all()
            fts_ok = (
                await conn.execute(
                    text(
                        "SELECT to_tsvector('english', 'react debug checklist') "
                        "@@ plainto_tsquery('english', 'react')"
                    )
                )
            ).scalar_one()
            trigram_score = (
                await conn.execute(
                    text("SELECT similarity('react debug checklist', 'react debug cheklist')")
                )
            ).scalar_one()

        _ensure(ext_present == 1, "pg_trgm extension is not installed")
        missing_indexes = sorted(required_indexes - set(index_rows))
        _ensure(not missing_indexes, f"Missing Postgres indexes: {missing_indexes}")
        _ensure(bool(fts_ok), "PostgreSQL full-text search operators are not working")
        _ensure(float(trigram_score) > 0.1, "PostgreSQL trigram similarity is not working")
        report.add_check("postgres_extensions_and_indexes")
        report.add_check("postgres_fts_and_trigram_primitives")

    report.add_check("schema_tables_and_columns")


async def _run_flow_validation(seed: SeedState) -> ValidationReport:
    report = ValidationReport()
    app = create_app()
    transport = ASGITransport(app=app)

    async with (
        AsyncClient(transport=transport, base_url="http://testserver") as anon_client,
        AsyncClient(transport=transport, base_url="http://testserver") as user_client,
        AsyncClient(transport=transport, base_url="http://testserver") as moderator_client,
        AsyncClient(transport=transport, base_url="http://testserver") as admin_client,
    ):
        await _api(report, anon_client, "GET", "/health", 200, label="healthcheck")
        await _api(report, anon_client, "GET", "/", 200, label="root_endpoint")
        await _api(report, anon_client, "GET", "/api/v1/users/me", 401, label="protected_requires_auth")
        await _api(report, anon_client, "GET", "/api/v1/missions", 401, label="missions_requires_auth")

        cors_preflight = await _api(
            report,
            anon_client,
            "OPTIONS",
            "/api/v1/auth/login",
            200,
            label="auth_cors_preflight_allowed_origin",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        _ensure(
            cors_preflight.headers.get("access-control-allow-origin") == "http://localhost:3000",
            "CORS allow-origin should match allowed frontend origin",
        )
        _ensure(
            cors_preflight.headers.get("access-control-allow-credentials") == "true",
            "CORS should allow credentials for cookie auth",
        )

        # Auth flow: register -> me -> refresh rotation.
        register_payload = {
            "email": "phase11.user@promptsvault.com",
            "password": "UserPass123!",
            "display_name": "Phase11 User",
        }
        register_resp = await _api(
            report,
            user_client,
            "POST",
            "/api/v1/auth/register",
            201,
            label="auth_register",
            json=register_payload,
            headers={"Origin": "http://localhost:3000"},
        )
        set_cookie = " ".join(register_resp.headers.get_list("set-cookie"))
        lower_set_cookie = set_cookie.lower()
        _ensure("httponly" in lower_set_cookie, "Auth cookies must be HttpOnly")
        _ensure("samesite=" in lower_set_cookie, "Auth cookies must define SameSite")
        if get_settings().auth_cookie_secure:
            _ensure("secure" in lower_set_cookie, "Secure auth cookie flag is required when enabled")
        _ensure("pv_access_token" in set_cookie and "pv_refresh_token" in set_cookie, "Auth cookies missing")
        me_resp = await _api(report, user_client, "GET", "/api/v1/users/me", 200, label="auth_session_me")
        user_id = me_resp.json()["id"]
        user_uuid = uuid.UUID(user_id)

        session_clone = AsyncClient(transport=transport, base_url="http://testserver")
        try:
            session_clone.cookies.update(user_client.cookies)
            await _api(
                report,
                session_clone,
                "GET",
                "/api/v1/users/me",
                200,
                label="auth_session_persistence_cookie_reuse",
            )
        finally:
            await session_clone.aclose()

        old_refresh = user_client.cookies.get(get_settings().refresh_token_cookie_name)
        await _api(report, user_client, "POST", "/api/v1/auth/refresh", 200, label="auth_refresh")
        new_refresh = user_client.cookies.get(get_settings().refresh_token_cookie_name)
        _ensure(old_refresh and new_refresh and old_refresh != new_refresh, "Refresh token did not rotate")

        # Reuse old refresh token must fail.
        old_refresh_client = AsyncClient(transport=transport, base_url="http://testserver")
        try:
            old_refresh_client.cookies.set(get_settings().refresh_token_cookie_name, old_refresh)
            reuse_resp = await _api(
                report,
                old_refresh_client,
                "POST",
                "/api/v1/auth/refresh",
                401,
                label="auth_refresh_reuse_prevented",
            )
            _ensure(reuse_resp.json().get("code") == "refresh_token_reused", "Expected refresh reuse protection")
        finally:
            await old_refresh_client.aclose()

        # Onboarding -> starter pack -> first win.
        profile_before = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/onboarding/profile",
            200,
            label="onboarding_profile_get_initial",
        )
        _ensure(profile_before.json()["needs_onboarding"] is True, "New user should need onboarding")
        await _api(
            report,
            user_client,
            "PUT",
            "/api/v1/onboarding/profile",
            200,
            label="onboarding_profile_update",
            json={"role": "student", "goal": "learning", "ai_context": "school"},
        )
        starter_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/onboarding/starter-pack",
            200,
            label="onboarding_starter_pack",
        )
        starter_pack = starter_resp.json()
        _ensure(3 <= len(starter_pack["prompts"]) <= 5, "Starter pack must contain 3-5 prompts")
        _ensure(starter_pack["lesson"] is not None, "Starter pack must include lesson")
        _ensure(starter_pack["action"] is not None, "Starter pack must include first action")

        first_win_prompt_id = starter_pack["action"]["prompt_id"]
        await _api(
            report,
            user_client,
            "POST",
            "/api/v1/onboarding/first-win",
            200,
            label="onboarding_first_win_complete",
            json={"prompt_id": first_win_prompt_id, "action": "copied"},
        )

        # Discovery and search.
        await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts/discovery-filters",
            200,
            label="discovery_filters",
        )
        discovery_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="discovery_search_filters",
            params={
                "q": "react debug checklist",
                "difficulty": "beginner",
                "use_case": "debugging",
                "model": "gpt-4o-mini",
                "tag": "react",
                "sort": "relevance",
                "limit": 10,
            },
        )
        items = discovery_resp.json()
        _ensure(len(items) >= 1, "Search should return at least one prompt")
        _ensure(all(item["difficulty"] == "beginner" for item in items), "Difficulty filter mismatch")
        typo_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="discovery_trigram_typo_search",
            params={"q": "react debug cheklist", "sort": "relevance", "limit": 10},
        )
        _ensure(
            any(item["slug"] == seed.free_prompt_slug for item in typo_resp.json()),
            "Typo-tolerant search should return the React debug prompt",
        )
        await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts/discovery-sections",
            200,
            label="discovery_sections",
        )
        await _api(
            report,
            user_client,
            "GET",
            f"/api/v1/prompts/by-slug/{seed.free_prompt_slug}/related",
            200,
            label="discovery_related_prompts",
        )

        # Pagination.
        page_1 = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="prompts_pagination_page1",
            params={"skip": 0, "limit": 2, "sort": "newest"},
        )
        page_2 = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="prompts_pagination_page2",
            params={"skip": 2, "limit": 2, "sort": "newest"},
        )
        _ensure(len(page_1.json()) <= 2 and len(page_2.json()) <= 2, "Pagination contract broken")

        # Prompt interactions + cache invalidation checks.
        reset_started = perf_counter()
        reset_resp = await user_client.delete(f"/api/v1/users/me/saved-prompts/{seed.free_prompt_id}")
        report.add_timing("saved_prompt_reset", (perf_counter() - reset_started) * 1000)
        _ensure(
            reset_resp.status_code in (204, 404),
            f"saved_prompt_reset: expected 204/404, got {reset_resp.status_code}, body={reset_resp.text}",
        )
        report.add_check("saved_prompt_reset")
        before_save_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="cache_before_save_list",
            params={"sort": "most_saved", "limit": 20},
        )
        before_map = {item["id"]: item["save_count"] for item in before_save_resp.json()}
        before_save_count = int(before_map.get(str(seed.free_prompt_id), 0))
        async with async_session_maker() as session:
            copy_before = int(
                (
                    await session.execute(
                        select(PromptStats.copy_count).where(PromptStats.prompt_id == seed.free_prompt_id)
                    )
                ).scalar_one()
                or 0
            )

        await _api(
            report,
            user_client,
            "POST",
            f"/api/v1/users/me/saved-prompts/{seed.free_prompt_id}",
            204,
            label="prompt_saved",
        )
        await _api(
            report,
            user_client,
            "POST",
            f"/api/v1/prompts/{seed.free_prompt_id}/events/copy",
            204,
            label="prompt_copied",
        )
        burst_count = 3
        burst_responses = await asyncio.gather(
            *[
                user_client.post(f"/api/v1/prompts/{seed.free_prompt_id}/events/copy")
                for _ in range(burst_count)
            ]
        )
        for idx, response in enumerate(burst_responses, start=1):
            _ensure(
                response.status_code == 204,
                f"prompt_copy_race_burst_{idx}: expected 204, got {response.status_code}, body={response.text}",
            )
            report.add_check(f"prompt_copy_race_burst_{idx}")

        after_save_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/prompts",
            200,
            label="cache_after_save_list",
            params={"sort": "most_saved", "limit": 20},
        )
        after_map = {item["id"]: item["save_count"] for item in after_save_resp.json()}
        after_save_count = int(after_map.get(str(seed.free_prompt_id), 0))
        _ensure(
            after_save_count >= before_save_count + 1,
            "Cache invalidation failed: save_count did not update after save",
        )
        async with async_session_maker() as session:
            copy_after = int(
                (
                    await session.execute(
                        select(PromptStats.copy_count).where(PromptStats.prompt_id == seed.free_prompt_id)
                    )
                ).scalar_one()
                or 0
            )
        _ensure(
            copy_after >= copy_before + 1 + burst_count,
            "Copy stats update is stale or lost under concurrent write burst",
        )
        report.add_check("prompt_copy_race_condition_guard")

        if VALIDATION_MODE == "real":
            redis_url = get_settings().redis_url
            _ensure(redis_url is not None, "real mode redis URL is missing")
            try:
                from redis.asyncio import Redis as AsyncRedis
            except Exception as exc:  # pragma: no cover
                raise AssertionError("redis client dependency is missing") from exc
            redis_client = AsyncRedis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            try:
                cursor = 0
                key_count = 0
                while True:
                    cursor, keys = await redis_client.scan(cursor=cursor, match="prompts-vault:*", count=200)
                    key_count += len(keys)
                    if cursor == 0:
                        break
                _ensure(key_count > 0, "Redis cache keys were not written")
            finally:
                await redis_client.aclose()
            report.add_check("redis_cache_writes_verified")

        saved_list = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/users/me/saved-prompts",
            200,
            label="saved_prompts_list",
        )
        _ensure(any(item["id"] == str(seed.free_prompt_id) for item in saved_list.json()), "Saved prompt missing")

        # Lessons -> completion -> mission progress/rewards.
        await _api(report, user_client, "GET", "/api/v1/lessons", 200, label="lessons_list")
        await _api(
            report,
            user_client,
            "GET",
            f"/api/v1/lessons/by-slug/{seed.lesson_slug}",
            200,
            label="lesson_detail",
        )
        await _api(
            report,
            user_client,
            "POST",
            f"/api/v1/lessons/by-slug/{seed.lesson_slug}/complete",
            204,
            label="lesson_complete",
        )

        missions_resp = await _api(report, user_client, "GET", "/api/v1/missions", 200, label="missions_list")
        missions_payload = missions_resp.json()
        _ensure(missions_payload["total_count"] >= 3, "Expected seeded missions")
        _ensure(missions_payload["completed_count"] >= 2, "Mission completion should reflect user actions")
        _ensure(
            missions_payload["rewards"]["credits"] >= 10 or len(missions_payload["rewards"]["badges"]) >= 1,
            "Mission rewards were not granted",
        )
        await _api(report, user_client, "GET", "/api/v1/missions/current", 200, label="missions_current")

        # Contributor funnel: submit -> moderation -> feedback -> profile.
        submit_resp = await _api(
            report,
            user_client,
            "POST",
            "/api/v1/contributions/submit",
            201,
            label="contribution_submit",
            json={
                "slug": "phase11-submission",
                "title": "React crash triage prompt",
                "summary": "Triage crashes with a repeatable debugging flow.",
                "body": (
                    "Act as a debugging lead. Given an error trace, identify probable root causes, "
                    "prioritize checks, provide quick mitigations, and finish with a verification checklist "
                    "that confirms the bug is fixed in staging."
                ),
                "category_id": str(seed.category_public_id),
                "technique": "few_shot",
                "difficulty": "intermediate",
                "output_type": "code",
                "use_cases": ["debugging"],
                "tags": ["react"],
                "model_compatibility": ["gpt-4o-mini"],
            },
        )
        submitted_id = submit_resp.json()["id"]

        my_submissions = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/users/me/submissions",
            200,
            label="contribution_status_user_view_pending",
        )
        _ensure(
            any(item["id"] == submitted_id and item["moderation_state"] == "pending" for item in my_submissions.json()),
            "Submission should appear as pending before moderation",
        )

        await _api(
            report,
            user_client,
            "GET",
            "/api/v1/moderation/queue",
            403,
            label="moderation_queue_forbidden_for_user",
        )

        await _api(
            report,
            moderator_client,
            "POST",
            "/api/v1/auth/login",
            200,
            label="moderator_login",
            json={"email": seed.moderator_email, "password": seed.moderator_password},
        )
        queue_resp = await _api(
            report,
            moderator_client,
            "GET",
            "/api/v1/moderation/queue",
            200,
            label="moderation_queue",
        )
        _ensure(any(item["id"] == submitted_id for item in queue_resp.json()), "Submission missing in moderation queue")

        await _api(
            report,
            moderator_client,
            "POST",
            f"/api/v1/moderation/{submitted_id}/decision",
            204,
            label="moderation_reject_with_reason",
            json={"action": "reject", "reason": "Needs clearer objective and output format."},
        )

        my_submissions_after = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/users/me/submissions",
            200,
            label="contribution_status_user_view_rejected",
        )
        rejected_rows = [row for row in my_submissions_after.json() if row["id"] == submitted_id]
        _ensure(rejected_rows and rejected_rows[0]["moderation_state"] == "rejected", "Rejection not reflected")
        _ensure(rejected_rows[0]["feedback_hints"], "Feedback hints should be provided after rejection")

        top_contributors_resp = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/contributors/top",
            200,
            label="contributors_top",
        )
        _ensure(len(top_contributors_resp.json()) >= 1, "Top contributors should not be empty")
        contributor_slug = top_contributors_resp.json()[0]["slug"]
        await _api(
            report,
            user_client,
            "GET",
            f"/api/v1/contributors/{contributor_slug}",
            200,
            label="contributor_profile_public",
        )

        # Monetization funnel: locked content -> checkout -> entitlement.
        async with async_session_maker() as session:
            await session.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(plan_tier=PlanTier.free, premium_unlock_until=None)
            )
            await session.commit()

        premium_locked = await _api(
            report,
            user_client,
            "GET",
            f"/api/v1/prompts/by-slug/{seed.premium_prompt_slug}",
            200,
            label="premium_prompt_locked_before_upgrade",
        )
        _ensure(premium_locked.json()["body_locked"] is True, "Premium prompt should be locked before upgrade")

        await _api(report, user_client, "GET", "/api/v1/billing/plans", 200, label="billing_plans")
        sub_before = await _api(
            report, user_client, "GET", "/api/v1/billing/subscription", 200, label="billing_status_before_upgrade"
        )
        _ensure(sub_before.json()["plan_tier"] == "free", "User must start on free plan")

        settings = get_settings()
        stripe_checkout_enabled = _stripe_checkout_configured()
        stripe_webhook_enabled = _stripe_webhook_configured()

        checkout_expected_status = 200 if settings.billing_mock_mode or stripe_checkout_enabled else 501
        checkout_label = (
            "billing_checkout_mock"
            if settings.billing_mock_mode
            else "billing_checkout_stripe" if stripe_checkout_enabled else "billing_checkout_not_configured_guard"
        )
        checkout_resp = await _api(
            report,
            user_client,
            "POST",
            "/api/v1/billing/checkout/session",
            checkout_expected_status,
            label=checkout_label,
            json={"tier": "starter"},
        )
        if checkout_expected_status == 200:
            checkout_payload = checkout_resp.json()
            _ensure(checkout_payload.get("url"), "Checkout response must include url")
            _ensure(checkout_payload.get("session_id"), "Checkout response must include session_id")

        sub_after_checkout = await _api(
            report,
            user_client,
            "GET",
            "/api/v1/billing/subscription",
            200,
            label="billing_status_after_checkout",
        )
        if settings.billing_mock_mode:
            _ensure(
                sub_after_checkout.json()["plan_tier"] == "starter",
                "Entitlement recalculation failed after mock upgrade",
            )
        elif checkout_expected_status == 501:
            _ensure(
                sub_after_checkout.json()["plan_tier"] == "free",
                "Plan tier should remain free when checkout is not configured",
            )

        premium_after_checkout = await _api(
            report,
            user_client,
            "GET",
            f"/api/v1/prompts/by-slug/{seed.premium_prompt_slug}",
            200,
            label="premium_prompt_after_checkout",
        )
        if settings.billing_mock_mode:
            _ensure(
                premium_after_checkout.json()["body_locked"] is False,
                "Premium prompt should unlock after mock checkout",
            )
        else:
            _ensure(
                premium_after_checkout.json()["body_locked"] is True,
                "Premium prompt should stay locked until Stripe webhook activation",
            )

        if settings.billing_mock_mode or stripe_checkout_enabled:
            portal_expected_status = 200
        elif settings.stripe_secret_key:
            portal_expected_status = 404
        else:
            portal_expected_status = 501
        await _api(
            report,
            user_client,
            "POST",
            "/api/v1/billing/portal",
            portal_expected_status,
            label=(
                "billing_portal"
                if portal_expected_status == 200
                else "billing_portal_missing_customer_guard"
                if portal_expected_status == 404
                else "billing_portal_not_configured_guard"
            ),
            json={},
        )
        await _api(
            report,
            user_client,
            "POST",
            "/api/v1/billing/checkout",
            410,
            label="billing_deprecated_checkout_contract",
        )
        await _api(
            report,
            user_client,
            "POST",
            "/api/v1/billing/webhooks",
            400 if stripe_webhook_enabled else 501,
            label="billing_webhook_missing_signature_guard"
            if stripe_webhook_enabled
            else "billing_webhook_not_configured_guard",
            json={"id": "evt_test"},
        )

        if stripe_webhook_enabled:
            webhook_event = _build_subscription_webhook_event(user_id=user_id)
            webhook_payload = json.dumps(webhook_event, separators=(",", ":"), sort_keys=True).encode("utf-8")
            signature = _build_stripe_signature_header(
                payload=webhook_payload,
                secret=str(settings.stripe_webhook_secret),
            )
            webhook_headers = {
                "content-type": "application/json",
                "stripe-signature": signature,
            }
            webhook_resp = await _api(
                report,
                user_client,
                "POST",
                "/api/v1/billing/webhooks",
                200,
                label="billing_webhook_signed_subscription_event",
                content=webhook_payload,
                headers=webhook_headers,
            )
            _ensure(webhook_resp.json().get("status") == "ok", "Signed webhook should be accepted")
            duplicate_webhook = await _api(
                report,
                user_client,
                "POST",
                "/api/v1/billing/webhooks",
                200,
                label="billing_webhook_duplicate_event",
                content=webhook_payload,
                headers=webhook_headers,
            )
            _ensure(duplicate_webhook.json().get("status") == "duplicate", "Duplicate webhook must be idempotent")
            sub_after_webhook = await _api(
                report,
                user_client,
                "GET",
                "/api/v1/billing/subscription",
                200,
                label="billing_status_after_webhook",
            )
            _ensure(
                sub_after_webhook.json()["plan_tier"] == "starter",
                "Stripe webhook should activate starter entitlement",
            )
            premium_after_webhook = await _api(
                report,
                user_client,
                "GET",
                f"/api/v1/prompts/by-slug/{seed.premium_prompt_slug}",
                200,
                label="premium_prompt_unlocked_after_webhook",
            )
            _ensure(
                premium_after_webhook.json()["body_locked"] is False,
                "Premium prompt should unlock after Stripe webhook subscription activation",
            )
        elif REQUIRE_STRIPE_WEBHOOK:
            report.add_blocker(
                "Stripe webhook validation required, but webhook credentials are not configured for this run"
            )

        # Analytics ingestion, dedup, schema validation.
        now_iso = datetime.now(timezone.utc).isoformat()
        event_batch = [
            {
                "event_id": f"phase11_{name}_{uuid.uuid4().hex[:10]}",
                "event_name": name,
                "session_id": "phase11-session",
                "timestamp": now_iso,
                "context": {"page": "/phase11", "feature": "validation"},
                "metadata": {"phase": "11", "step": name.replace("_", "")},
                "source": "web",
                "attribution": {
                    "utm_source": "qa",
                    "utm_medium": "validation",
                    "utm_campaign": "phase11",
                    "referrer": "https://example.test/qa",
                },
            }
            for name in (
                "onboarding_completed",
                "prompt_viewed",
                "prompt_copied",
                "prompt_saved",
                "mission_started",
                "mission_completed",
                "submission_created",
                "upgrade_clicked",
                "checkout_started",
                "subscription_activated",
            )
        ]
        analytics_ingest = await _api(
            report,
            user_client,
            "POST",
            "/api/v1/analytics/events",
            202,
            label="analytics_ingest_batch",
            json={"events": event_batch},
        )
        ingest_payload = analytics_ingest.json()
        _ensure(ingest_payload["accepted"] == len(event_batch), "Analytics accepted mismatch")
        _ensure(ingest_payload["ingested"] == len(event_batch), "Analytics ingested mismatch")

        duplicate_event = dict(event_batch[0])
        duplicate_resp = await _api(
            report,
            user_client,
            "POST",
            "/api/v1/analytics/events",
            202,
            label="analytics_duplicate_event_rejected",
            json={"event": duplicate_event},
        )
        duplicate_payload = duplicate_resp.json()
        _ensure(
            duplicate_payload["duplicates"] >= 1 and duplicate_payload["ingested"] == 0,
            "Analytics duplicate detection failed",
        )
        await _api(
            report,
            user_client,
            "POST",
            "/api/v1/analytics/events",
            422,
            label="analytics_schema_validation",
            json={"event": duplicate_event, "events": [duplicate_event]},
        )
        # Admin authz path.
        await _api(
            report,
            user_client,
            "PATCH",
            f"/api/v1/admin/users/{user_id}/tier",
            403,
            label="admin_forbidden_for_user",
            json={"plan_tier": "pro"},
        )
        await _api(
            report,
            admin_client,
            "POST",
            "/api/v1/auth/login",
            200,
            label="admin_login",
            json={"email": seed.admin_email, "password": seed.admin_password},
        )
        await _api(
            report,
            admin_client,
            "PATCH",
            f"/api/v1/admin/users/{user_id}/tier",
            200,
            label="admin_update_user_tier",
            json={"plan_tier": "starter"},
        )
        await _api(
            report,
            admin_client,
            "GET",
            "/api/v1/analytics/events/recent",
            200,
            label="analytics_recent_events_admin",
            params={"limit": 100},
        )

        # Rate limiting smoke test.
        for attempt in range(8):
            await _api(
                report,
                anon_client,
                "POST",
                "/api/v1/auth/login",
                401,
                label=f"auth_login_invalid_attempt_{attempt + 1}",
                json={"email": "phase11.user@promptsvault.com", "password": "bad-password"},
            )
        await _api(
            report,
            anon_client,
            "POST",
            "/api/v1/auth/login",
            429,
            label="auth_login_rate_limited",
            json={"email": "phase11.user@promptsvault.com", "password": "bad-password"},
        )

        # Logout + post-logout protection.
        await _api(report, user_client, "POST", "/api/v1/auth/logout", 204, label="auth_logout")
        await _api(report, user_client, "GET", "/api/v1/users/me", 401, label="auth_post_logout_protected")
        await _api(report, user_client, "POST", "/api/v1/auth/refresh", 401, label="auth_post_logout_refresh")

    return report


async def _validate_data_integrity(report: ValidationReport) -> None:
    async with async_session_maker() as session:
        duplicate_analytics = (
            await session.execute(
                select(AnalyticsEvent.event_id)
                .group_by(AnalyticsEvent.event_id)
                .having(func.count(AnalyticsEvent.id) > 1)
            )
        ).scalars().all()
        _ensure(not duplicate_analytics, f"Duplicate analytics event_id rows found: {duplicate_analytics}")

        total_events = int((await session.execute(select(func.count()).select_from(AnalyticsEvent))).scalar_one() or 0)
        _ensure(total_events > 0, "Analytics table should contain ingested events")

    report.add_check("data_integrity_checks")


async def main() -> None:
    report = ValidationReport()
    print(f"phase11: mode={VALIDATION_MODE}")
    await _validate_runtime_configuration(report)
    await _validate_runtime_dialect_paths(report)

    print("phase11: reset schema")
    await _reset_schema()
    print("phase11: seed data")
    seed = await _seed_data()
    await _validate_schema(report)

    print("phase11: execute end-to-end flows")
    flow_report = await _run_flow_validation(seed)
    report.checks.extend(flow_report.checks)
    report.perf_ms.extend(flow_report.perf_ms)
    report.blockers.extend(flow_report.blockers)

    print("phase11: verify data integrity")
    await _validate_data_integrity(report)

    slow = report.slow_checks()
    print("")
    print("=== PHASE 11 VALIDATION SUMMARY ===")
    print(f"checks_passed={len(report.checks)}")
    print(f"timed_calls={len(report.perf_ms)}")
    print(f"slow_calls(>=700ms)={len(slow)}")
    print(f"blockers={len(report.blockers)}")
    if slow:
        for name, ms in sorted(slow, key=lambda row: row[1], reverse=True)[:10]:
            print(f"  {name}: {ms:.2f}ms")
    if report.blockers:
        for blocker in report.blockers:
            print(f"  blocker: {blocker}")
        raise AssertionError("phase11 validation blocked")
    print("status=ok")


if __name__ == "__main__":
    asyncio.run(main())
