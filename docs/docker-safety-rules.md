# Docker Safety Rules

Use the canonical root compose file only:

- Run `docker compose up --build` from [docker-compose.yml](/C:/Users/14/Desktop/PROJECTS/WEBSITE/docker-compose.yml).
- Do not set `COMPOSE_PROJECT_NAME`, do not use `-p`, and do not copy the stack into another compose project name.
- Do not point the API at `localhost`, `127.0.0.1`, `host.docker.internal`, or port `55432` when `APP_ENV=docker`.
- Do not add alternate Postgres port mappings for this repo.

Why this is now safe:

- The compose project name is pinned to `website`.
- Service `container_name` values are fixed (`website-db`, `website-api`, `website-web`, `website-redis`), so a second compose stack for this repo cannot start in parallel.
- The backend refuses to boot unless it is connected to the canonical `prompts_vault` database on `db:5432`, the schema is `public`, the Alembic head matches the repo, and the Store/Wallet tables exist.
- The backend also probes known fallback targets and fails if an alternate reachable Postgres accepts the app credentials.
- `python backend/scripts/docker_safety_check.py --mode static` validates the compose file, and `--mode runtime` checks the live Docker runtime for legacy DB ports or legacy stack names.
