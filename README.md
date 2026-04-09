# Prompts Vault

Monorepo with a clear top-level layout:

- `frontend/` - Next.js web app
- `backend/` - FastAPI service
- `docs/` - architecture and operational notes
- `.github/workflows/` - CI pipelines
- `docker-compose.yml` - local multi-service runtime
- `env.example` - environment template for local setup
- `pytest.ini` - shared pytest defaults for backend tests

## Quick Start

1. Backend:

```bash
cd backend
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

2. Frontend (new terminal):

```bash
cd frontend
npm install
npm run dev
```

3. Docker option (from repo root):

```bash
docker compose up --build
```

## Repository Conventions

- Keep product code inside `frontend/` and `backend/`.
- Keep docs in `docs/`.
- Avoid committing local IDE/workspace files (`.idea`, `.vscode`) and machine-specific temporary artifacts.

## Deployment

- Ubuntu 22.04 without domain (by server IP): see [docs/deploy-ubuntu-no-domain.md](docs/deploy-ubuntu-no-domain.md)
