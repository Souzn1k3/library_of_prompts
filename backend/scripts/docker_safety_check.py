from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CANONICAL_PROJECT = "website"
CANONICAL_DB_CONTAINER = "website-db"
LEGACY_CONTAINER_NAMES = {"site-db", "site-db-1", "prompts-vault-validation-db"}
REQUIRED_COMPOSE_SNIPPETS = {
    "project_name": "name: website",
    "db_container": "container_name: website-db",
    "redis_container": "container_name: website-redis",
    "api_container": "container_name: website-api",
    "web_container": "container_name: website-web",
    "db_name": "POSTGRES_DB: prompts_vault",
    "api_database_url": "DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/prompts_vault",
    "pgdata_volume": "name: website_pv_pgdata",
    "redis_volume": "name: website_redis_data",
}
FORBIDDEN_COMPOSE_SNIPPETS = {
    "legacy_db_port": '"55432:5432"',
    "docker_localhost_db": "DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/",
    "docker_loopback_db": "DATABASE_URL: postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/",
    "legacy_validation_db": "prompts_vault_validation",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def compose_file() -> Path:
    return repo_root() / "docker-compose.yml"


def _fail(message: str) -> None:
    raise RuntimeError(message)


def validate_compose_text(compose_text: str) -> None:
    for label, snippet in REQUIRED_COMPOSE_SNIPPETS.items():
        if snippet not in compose_text:
            _fail(f"Compose safety check failed: missing canonical {label} snippet.")

    for label, snippet in FORBIDDEN_COMPOSE_SNIPPETS.items():
        if snippet in compose_text:
            _fail(f"Compose safety check failed: found forbidden {label} snippet.")


def _run_docker_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _parse_docker_ps() -> list[dict[str, str]]:
    result = _run_docker_command(["docker", "ps", "--format", "{{json .}}"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        _fail(f"Runtime docker safety check failed to query docker ps: {details}")

    rows: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def validate_runtime_containers(rows: list[dict[str, str]]) -> None:
    names = {row.get("Names", "") for row in rows}
    legacy_names = sorted(name for name in names if name in LEGACY_CONTAINER_NAMES or name.startswith("site-"))
    if legacy_names:
        _fail(
            "Runtime docker safety check found legacy containers that can reintroduce the old stack: "
            + ", ".join(legacy_names)
        )

    published_postgres = []
    legacy_port_publishers = []
    for row in rows:
        name = row.get("Names", "")
        ports = row.get("Ports", "")
        if "->5432/tcp" in ports:
            published_postgres.append(name)
        if ":55432->5432/tcp" in ports or "0.0.0.0:55432->5432/tcp" in ports:
            legacy_port_publishers.append(name)

    if legacy_port_publishers:
        _fail(
            "Runtime docker safety check found forbidden legacy Postgres port 55432 on: "
            + ", ".join(sorted(legacy_port_publishers))
        )

    if len(published_postgres) > 1:
        _fail(
            "Runtime docker safety check found multiple published Postgres containers: "
            + ", ".join(sorted(published_postgres))
        )

    if CANONICAL_DB_CONTAINER in names and published_postgres != [CANONICAL_DB_CONTAINER]:
        _fail(
            "Runtime docker safety check expected the canonical db container to be the only published Postgres instance."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical Docker safety rules for Prompts Vault.")
    parser.add_argument(
        "--mode",
        choices=("static", "runtime", "all"),
        default="static",
        help="Run compose file checks only, live docker runtime checks only, or both.",
    )
    args = parser.parse_args()

    if args.mode in {"static", "all"}:
        validate_compose_text(compose_file().read_text(encoding="utf-8"))
        print("docker-safety: static checks passed")

    if args.mode in {"runtime", "all"}:
        validate_runtime_containers(_parse_docker_ps())
        print("docker-safety: runtime checks passed")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
