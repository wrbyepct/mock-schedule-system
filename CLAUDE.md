# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`shift_scheduler` — a shift scheduling system that enforces Taiwan's 勞基法 (Labor Standards Act) 變形工時 (flexible working hours) rules. See `SPEC.md` for the full specification and active development spikes.

## Commands

All commands use `uv`. The `.venv` is at the project root.

```bash
# Install dependencies
uv sync

# Run the development server
uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/path/to/test_file.py

# Run a single test
uv run pytest tests/path/to/test_file.py::test_function_name

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy app/

# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Docker
docker build -t shift_scheduler .
docker run --env-file .env shift_scheduler uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Architecture

**Domain-driven folder structure**: code is grouped by domain under `app/` — each domain has `models.py`, `schemas.py`, `service.py`, `router.py`, `dependencies.py`, `exceptions.py`. The domains are: `organizations`, `auth`, `employees`, `shifts`, `preferences`, `schedules`, `leaves`, `violations`.

**`app/core/`**: shared infrastructure only — config, database engine/session factory, JWT/security, shared FastAPI dependencies. No business logic lives here.

**`violations/rules/`**: pure functions with no DB access or side effects. Each file handles one rule category (daily hours, consecutive days, rest days, shift interval). Designed for TDD with no test infrastructure needed.

**`app/core/config.py`**: `pydantic-settings` `Settings` class reads from `.env`. Import `from app.core.config import settings` anywhere. Never use `os.environ.get()`.

**Celery**: one Dockerfile, two docker-compose services. The `api` service runs uvicorn; the `worker` service runs `celery -A app.celery_app worker`. Schedule generation and Excel export run as background tasks.

**Database**: SQLAlchemy async engine with `asyncpg`. Always use `create_async_engine`, `AsyncSession`, `async_sessionmaker`. Alembic handles migrations with an async `env.py`.

**Tests** mirror the `app/` domain structure under `tests/`.

## Key Domain Rules

- **Always include `organization_id`** on every new domain model — required for future multi-tenant migration even though on-premise deployments are single-tenant.
- **`例假` vs `休息日` must be distinct `DayType` values** — violation detection breaks if merged into a boolean.
- **`DATABASE_URL` must use `postgresql+asyncpg://`** scheme — the plain `postgresql://` scheme only works with the sync engine.
- **Employee preferences**: `UNAVAILABLE` = hard constraint (schedule invalid if violated); `PREFERRED` = soft constraint (schedule suboptimal if violated).
- **Cycle window start date** must be admin-configurable per employee group — required for 雙週/四週/八週 violation detection.

## Development Methodology

DDD + TDD. See `SPEC.md` Section 6 for the current active spikes. Do not move to the next spike until all acceptance criteria of the current one are checked off.
