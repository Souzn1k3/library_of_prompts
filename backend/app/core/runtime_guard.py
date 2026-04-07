from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path

import asyncpg
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CANONICAL_TABLES = frozenset(
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
)


@dataclass(frozen=True)
class DatabaseRuntimeState:
    database_name: str
    schema_name: str
    alembic_heads: tuple[str, ...]
    table_names: frozenset[str]


def expected_alembic_heads() -> tuple[str, ...]:
    config = AlembicConfig(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    heads = tuple(sorted(ScriptDirectory.from_config(config).get_heads()))
    if not heads:
        raise RuntimeError("Runtime guard could not determine the expected Alembic head revision.")
    return heads


def validate_database_state(
    settings: Settings,
    state: DatabaseRuntimeState,
    *,
    expected_heads: tuple[str, ...] | None = None,
) -> None:
    if state.database_name != settings.expected_database_name:
        raise RuntimeError(
            "Runtime guard detected the wrong database. "
            f"Expected '{settings.expected_database_name}', got '{state.database_name}'."
        )
    if state.schema_name != settings.expected_database_schema:
        raise RuntimeError(
            "Runtime guard detected the wrong schema. "
            f"Expected '{settings.expected_database_schema}', got '{state.schema_name}'."
        )

    missing_tables = sorted(REQUIRED_CANONICAL_TABLES - state.table_names)
    if missing_tables:
        raise RuntimeError(
            "Runtime guard detected a non-canonical schema. Missing required tables: "
            + ", ".join(missing_tables)
        )

    expected = tuple(sorted(expected_heads or expected_alembic_heads()))
    actual = tuple(sorted(state.alembic_heads))
    if actual != expected:
        raise RuntimeError(
            "Runtime guard detected an Alembic revision mismatch. "
            f"Expected {expected}, got {actual}."
        )


async def collect_database_state(engine: AsyncEngine, schema_name: str) -> DatabaseRuntimeState:
    async with engine.begin() as conn:
        database_name = await conn.scalar(text("SELECT current_database()"))
        current_schema = await conn.scalar(text("SELECT current_schema()"))
        normalized_schema = str(current_schema or schema_name)
        table_names = await conn.run_sync(
            lambda sync_conn: frozenset(inspect(sync_conn).get_table_names(schema=normalized_schema))
        )
        alembic_heads: tuple[str, ...] = ()
        if "alembic_version" in table_names:
            versions = await conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
            alembic_heads = tuple(versions.scalars().all())

    return DatabaseRuntimeState(
        database_name=str(database_name or ""),
        schema_name=normalized_schema,
        alembic_heads=alembic_heads,
        table_names=table_names,
    )


async def _probe_postgres_target(settings: Settings, host: str, port: int) -> str | None:
    url = settings.parsed_database_url
    if not url.username:
        return None

    # asyncpg DNS resolver can occasionally emit "Future exception was never retrieved"
    # for unreachable hostnames in probe lists. Resolve first and skip unresolvable hosts.
    resolved_host = host
    try:
        ipaddress.ip_address(host)
    except ValueError:
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.getaddrinfo(host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
        except OSError:
            return None
        if not addr_info:
            return None
        resolved_host = str(addr_info[0][4][0])

    try:
        connection = await asyncpg.connect(
            host=resolved_host,
            port=port,
            user=url.username,
            password=url.password,
            database="postgres",
            timeout=1.0,
        )
    except (
        asyncio.TimeoutError,
        OSError,
        asyncpg.CannotConnectNowError,
        asyncpg.InvalidAuthorizationSpecificationError,
        asyncpg.InvalidCatalogNameError,
        asyncpg.InvalidPasswordError,
        asyncpg.PostgresError,
    ):
        return None

    try:
        database_name = await connection.fetchval("SELECT current_database()")
    finally:
        await connection.close()
    return str(database_name or "postgres")


async def detect_duplicate_postgres_targets(settings: Settings) -> tuple[str, ...]:
    if settings.app_env != "docker" or not settings.duplicate_db_detection_enabled:
        return ()

    canonical_host = (settings.expected_database_host or "").lower()
    canonical_port = int(settings.expected_database_port or 0)
    matches: list[str] = []

    for host in settings.duplicate_db_probe_host_list:
        for port in settings.duplicate_db_probe_port_list:
            if host == canonical_host and port == canonical_port:
                continue
            database_name = await _probe_postgres_target(settings, host, port)
            if database_name is not None:
                matches.append(f"{host}:{port}/{database_name}")

    if matches:
        raise RuntimeError(
            "Runtime guard found additional reachable PostgreSQL targets that accept the app credentials: "
            + ", ".join(matches)
        )
    return ()


async def verify_runtime_database(engine: AsyncEngine, settings: Settings) -> None:
    if settings.app_env == "validation" or not settings.startup_db_validation_enabled:
        return

    state = await collect_database_state(engine, settings.expected_database_schema)
    validate_database_state(settings, state)
    await detect_duplicate_postgres_targets(settings)
    log.info(
        "runtime_guard_passed",
        app_env=settings.app_env,
        compose_project=settings.canonical_compose_project,
        database_name=state.database_name,
        schema_name=state.schema_name,
        alembic_heads=list(state.alembic_heads),
    )
