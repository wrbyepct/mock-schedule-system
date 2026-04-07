# shift_scheduler — Project Specification & Development Record

> Last updated: 2026-04-07
> Status: Phase 1 — Project Skeleton (In Progress)

---

## How to Use This Document

This document is the single source of truth for the `shift_scheduler` project.
It is written for two audiences:

- **Junior developers joining the team**: Read Sections 1–5 first to understand
  what the system does and why decisions were made. Then pick up any spike
  from Section 6 — each spike is fully self-contained.

- **AI agents**: Each spike in Section 6 contains everything needed to complete
  the task in isolation. You do not need to read the full document to execute
  a spike. Start from the spike's "Context" block and follow the
  "Acceptance Criteria" exactly.

**Development rule**: Do not move to the next spike until all acceptance
criteria of the current spike are checked off. Each spike builds on the previous.

---

## Table of Contents

1. Project Overview
2. Deployment Strategy
3. Tech Stack
4. Architecture
5. Domain Decisions
6. Development Spikes (Phase 1 — Skeleton)
7. Known Blind Spots
8. Open / TBD Items

---

## 1. Project Overview

`shift_scheduler` is a general-purpose shift scheduling system designed to
comply with all 變形工時 (flexible working hours) rules under Taiwan's 勞基法
(Labor Standards Act).

**What it does:**
- Allows employees to submit shift preferences (hard unavailability and
  soft preferences) and leave applications
- Allows admins to auto-generate optimized schedules based on employee
  preferences and workforce requirements
- Automatically detects violations of 勞基法 變形工時 scheduling rules
- Supports Excel export of finalized schedules
- Sends notifications (channel TBD) for key events like leave approvals
  and schedule publication

**What it does NOT do (at launch):**
- Enforce leave quotas or balances (future plan)
- Support department-level grouping (future plan)
- Handle payroll or wage calculation

---

## 2. Deployment Strategy

**Current**: On-premise deployment. Each client organization runs their own
isolated Docker instance on their own server. Multi-tenancy is achieved
through physical isolation — each instance serves one organization.

**Future**: The system may migrate to a shared deployment where multiple
organizations share one instance. To make this migration painless, every
domain table includes an `organization_id` foreign key column from day one,
even though it is not actively used for filtering in on-premise deployments.
When shared deployment arrives, the column is already there — only
enforcement logic needs to be added.

**Why this matters for developers**: Always include `organization_id` when
creating any new domain model. Never skip it assuming "this deployment is
single-tenant anyway."

---

## 3. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend framework | FastAPI (async) | High performance async API, excellent DI system |
| ORM | SQLModel + SQLAlchemy 2.0 (async) | Combines Pydantic models with SQLAlchemy power |
| Database | PostgreSQL | Robust, production-grade relational DB |
| Async DB driver | asyncpg | Required by SQLAlchemy async engine for PostgreSQL |
| Migrations | Alembic | Standard SQLAlchemy migration tool |
| Task queue | Celery | Background jobs: schedule generation, Excel export, notifications |
| Message broker / cache | Redis | Celery broker + result backend |
| Data validation | Pydantic v2 (via SQLModel) | Request/response validation and settings management |
| Settings management | pydantic-settings | Typed, validated environment variable loading |
| Testing | pytest + pytest-asyncio | Async-compatible testing framework |
| Containerization | Docker + Docker Compose | Local dev and on-premise deployment |
| Package manager | uv | Fast, modern Python package manager |
| Linting | ruff | Fast Python linter and formatter |
| Type checking | mypy | Static type checking |

**Development methodology**: DDD (Domain-Driven Design) + TDD (Test-Driven Development)

---

## 4. Architecture

### 4.1 Folder Structure

```
shift_scheduler/
├── docker-compose.yml
├── .env.example                 <- template for required env vars, safe to commit
├── .gitignore
├── pyproject.toml               <- dependencies, ruff, mypy config
├── Dockerfile                   <- single image for both API and Celery worker
├── alembic/
│   ├── env.py                   <- async-compatible Alembic config
│   └── versions/                <- auto-generated migration files
│
├── app/
│   ├── __init__.py
│   ├── main.py                  <- FastAPI app factory, lifespan, router registration
│   ├── celery_app.py            <- Celery instance and configuration
│   │
│   ├── core/                    <- shared infrastructure, belongs to no single domain
│   │   ├── __init__.py
│   │   ├── config.py            <- pydantic-settings Settings class
│   │   ├── database.py          <- async engine, session factory, get_db_session
│   │   ├── dependencies.py      <- get_current_user, shared FastAPI dependencies
│   │   ├── exceptions.py        <- base domain exception classes
│   │   ├── security.py          <- JWT creation/verification, password hashing
│   │   └── celery_tasks.py      <- shared Celery task utilities
│   │
│   ├── organizations/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── auth/
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── employees/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── shifts/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── preferences/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── schedules/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── router.py
│   │   └── tasks.py             <- Celery tasks: schedule generation + Excel export
│   │
│   ├── leaves/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   └── violations/
│       ├── models.py
│       ├── schemas.py
│       ├── service.py
│       ├── rules/               <- pure functions, one file per rule category
│       │   ├── __init__.py
│       │   ├── daily_hours.py
│       │   ├── consecutive_days.py
│       │   ├── rest_days.py
│       │   └── shift_interval.py
│       ├── dependencies.py
│       ├── exceptions.py
│       └── router.py
│
└── tests/                       <- mirrors the app/ domain structure
    ├── conftest.py
    ├── organizations/
    ├── auth/
    ├── employees/
    ├── shifts/
    ├── preferences/
    ├── schedules/
    ├── leaves/
    └── violations/
```

### 4.2 Key Architecture Decisions

**Domain-driven folder structure**
Files are grouped by domain (employees, schedules, leaves) not by file type
(models, schemas, services). Adding a new feature touches one folder,
not five scattered directories.

**`core/` for shared infrastructure**
Anything that does not belong to a single domain lives in `core/`.
No business logic lives here.

**`violations/rules/` as pure functions**
Each rule file contains plain Python functions that take a schedule and
return a list of violations. No database access, no FastAPI, no side effects.
Trivially testable with TDD — no test infrastructure needed.

**One Dockerfile, two docker-compose services**
```yaml
api:
  build: .
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000

worker:
  build: .
  command: celery -A app.celery_app worker --loglevel=info
```

**Single `.env` file with section comments**
Split `.env` files were considered and rejected — they add tooling
complexity without meaningful benefit at this project's scale.

---

## 5. Domain Decisions

### 5.1 RBAC (Roles)

| Role | Permissions |
|---|---|
| `staff` | Submit preferences, apply for leave, select daily shift, view own schedule |
| `admin` | Everything staff can do, plus: generate pre-schedule, generate final schedule, modify final schedule, approve/reject leave applications |

### 5.2 變形工時 (Flexible Working Hours)

All four types supported. Assigned per employee individually.

| Type | Daily limit | Cycle | Min rest days in cycle |
|---|---|---|---|
| 一例一休 (standard) | 8 hrs | 7 days | 1 例假 + 1 休息日 |
| 雙週 | 10 hrs | 14 days | 2 例假 + 2 休息日 |
| 四週 | 10 hrs | 28 days | 4 例假 + 4 休息日 |
| 八週 | 8 hrs | 56 days | 8 例假 + 8 休息日 |

**Critical distinction**:
- `例假`: Mandatory rest. Scheduling anyone on this day is illegal.
- `休息日`: Can be worked, but triggers overtime pay rules.

These must be modelled as distinct DayType values — never as a single boolean.

**Cycle window start date**: Must be admin-configurable per employee group.

### 5.3 Shifts

- Admins define shift templates per organization (name + exact start/end time)
- No hardcoded shift types — no assumed 早班/中班/晚班
- Generated schedule assigns one specific shift template to each employee per day
- Required to enforce the 11-hour shift-change interval rule (勞基法 Article 34)

### 5.4 Employee Preferences

| Type | Meaning | Effect on optimizer |
|---|---|---|
| `UNAVAILABLE` | Hard constraint — cannot work this date | Schedule is invalid if violated |
| `PREFERRED` | Soft constraint — prefers this shift | Schedule is suboptimal if violated |

### 5.5 Leaves

Applied independently of the schedule. 14 types at launch, no quota
enforcement at launch (future plan):

```python
class LeaveType(str, Enum):
    marriage = "marriage"                    # 婚假
    bereavement = "bereavement"              # 喪假
    sick = "sick"                            # 普通傷病假
    personal = "personal"                    # 事假
    official = "official"                    # 公假
    occupational_sick = "occupational_sick"  # 公傷病假
    annual = "annual"                        # 特別休假
    menstrual = "menstrual"                  # 生理假
    maternity = "maternity"                  # 產假
    prenatal = "prenatal"                    # 產檢假
    paternity = "paternity"                  # 陪產檢及陪產假
    pregnancy_care = "pregnancy_care"        # 安胎假
    parental_leave = "parental_leave"        # 育嬰留職停薪
    family_care = "family_care"              # 家庭照顧假
```

### 5.6 Schedule Generation

- Triggered by admin, runs as a Celery background task
- Treats `UNAVAILABLE` as hard constraints, `PREFERRED` as soft constraints
- Input date range: TBD

### 5.7 Violation Detection

Automatically runs after schedule generation. Detects:
- Daily hour limit exceeded (varies by employee's 變形工時 type)
- Consecutive work days exceeded
- Insufficient rest days within the cycle window
- Less than 11-hour interval between shift changes (勞基法 Article 34)

### 5.8 Export

- Final schedule exportable as Excel via Celery background task

### 5.9 Notifications

- Will exist for key events (leave approval, schedule published)
- Delivery channel TBD — implemented as Celery tasks from day one

### 5.10 Departments

- Feature TBD
- `department_id` added as nullable foreign key on Employee from day one

---

## 6. Development Spikes — Phase 1: Project Skeleton

**Completion rule**: All acceptance criteria must be checked off before
moving to the next spike. Each spike is self-contained.

---

### Spike 1 — Project metadata and dependency declaration

**Status**: ☐ Not started

**Goal**:
Establish the project's Python package configuration and declare all
required dependencies before any code is written.

**Context**:
We use `uv` as the package manager (not pip or poetry). `pyproject.toml`
is the single source of truth for the project name, Python version,
all dependencies, and tooling configuration (ruff, mypy). Nothing else
can be built until this exists.

The `.env` file must never be committed to git — only `.env.example`
is committed so other developers know what variables to fill in.

**Acceptance Criteria**:
- [ ] `pyproject.toml` exists at the project root with:
        - Project name: `shift_scheduler`
        - Python version: `>=3.12`
        - Runtime dependencies:
          `fastapi`, `uvicorn`, `sqlmodel`, `sqlalchemy`,
          `asyncpg`, `alembic`, `pydantic-settings`,
          `celery`, `redis`, `python-multipart`
        - Dev dependencies:
          `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`
        - Ruff configured for linting and formatting
        - Mypy configured for strict type checking

- [ ] `.gitignore` covers at minimum:
        `.env`, `__pycache__/`, `.mypy_cache/`,
        `.ruff_cache/`, `*.pyc`, `.venv/`

- [ ] `.env.example` exists with clearly sectioned placeholders:

        # --- App ---
        APP_ENV=development
        DEBUG=true

        # --- Database ---
        DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shift_scheduler

        # --- Redis ---
        REDIS_URL=redis://localhost:6379/0

        # --- JWT ---
        JWT_SECRET_KEY=your-secret-key-here
        JWT_ALGORITHM=HS256
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

        # --- Celery ---
        CELERY_BROKER_URL=redis://localhost:6379/0
        CELERY_RESULT_BACKEND=redis://localhost:6379/0

- [ ] `uv sync` runs without errors
- [ ] `uv run ruff check .` runs without errors
- [ ] `.env` is NOT committed to the repository

**Notes**:
- `asyncpg` is the async PostgreSQL driver required by SQLAlchemy's
  async engine. Without it, database connections will fail at runtime.
- `DATABASE_URL` must use the `postgresql+asyncpg://` scheme —
  the plain `postgresql://` scheme only works with the sync engine.
- `python-multipart` is required by FastAPI for form data handling,
  used in the OAuth2 login endpoint.

---

### Spike 2 — Environment configuration and settings management

**Status**: ☐ Not started

**Depends on**: Spike 1 (pyproject.toml and .env.example must exist)

**Goal**:
Expose all environment variables as a typed, validated settings object
that any part of the app can import.

**Context**:
We use `pydantic-settings` to manage configuration. It reads the `.env`
file and validates values at startup using Pydantic. If a required
variable is missing or the wrong type, the app refuses to start with
a clear error — instead of failing silently at runtime.

All settings are exposed as a single `settings` singleton. Import it
anywhere with `from app.core.config import settings`. It is created
once at module load time — not re-read on every import.

**File to create**: `app/core/config.py`

**Acceptance Criteria**:
- [ ] `app/core/config.py` exists with a `Settings` class that:
        - Inherits from `pydantic_settings.BaseSettings`
        - Declares all variables from `.env.example` with correct types:
          `APP_ENV: str`, `DEBUG: bool`,
          `DATABASE_URL: str`, `REDIS_URL: str`,
          `JWT_SECRET_KEY: str`, `JWT_ALGORITHM: str`,
          `JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int`,
          `CELERY_BROKER_URL: str`, `CELERY_RESULT_BACKEND: str`
        - Reads from `.env` via:
          `model_config = SettingsConfigDict(env_file=".env")`

- [ ] A module-level `settings` instance exists at the bottom of `config.py`:
        from app.core.config import settings  # works from anywhere

- [ ] Starting the app with a missing required variable raises a clear
      `ValidationError` at import time — not silently later

- [ ] `DEBUG` correctly parses the string `"true"` from `.env`
      as Python `True`

**Notes**:
- Never use `os.environ.get()` in the codebase. Always use `settings`.
- pydantic-settings automatically coerces bool fields from strings
  like "true", "false", "1", "0" — no manual parsing needed.
- Treat the `settings` object as read-only after creation.

---

### Spike 3 — Application Dockerfile

**Status**: ☐ Not started

**Depends on**: Spike 1 (pyproject.toml must exist)

**Goal**:
Build a single Docker image that runs both the FastAPI app and the
Celery worker depending on the command passed at runtime.

**Context**:
One Dockerfile serves two purposes. The API and Celery worker share
the same codebase and dependencies so they share one image.
docker-compose runs them as separate services with different commands:

    api:    uvicorn app.main:app --host 0.0.0.0 --port 8000
    worker: celery -A app.celery_app worker --loglevel=info

We use a multi-stage build to keep the final image small:
- Stage 1 (builder): installs all dependencies via uv
- Stage 2 (runtime): copies only installed packages and app code

The image never contains a `.env` file. Environment variables are
injected at runtime by docker-compose via the `env_file` directive.

**File to create**: `Dockerfile` at the project root

**Acceptance Criteria**:
- [ ] `Dockerfile` exists at the project root
- [ ] Uses `python:3.12-slim` as the base image for the runtime stage
- [ ] Multi-stage build:
        - Stage 1 (builder): installs dependencies via `uv`
        - Stage 2 (runtime): copies only the virtualenv and app code
- [ ] Runtime stage creates and runs as a non-root user — never root
- [ ] No `.env` file is copied into the image at any stage
- [ ] `docker build -t shift_scheduler .` completes without errors
- [ ] Running the built image with:
        docker run --env-file .env shift_scheduler \
          uvicorn app.main:app --host 0.0.0.0 --port 8000
      starts without import errors (even if DB is not connected yet)

**Notes**:
- Copy `pyproject.toml` and install dependencies before copying app
  code. This lets Docker cache the dependency layer and skip
  reinstallation when only app code changes.
- The runtime stage must not contain uv, build tools, or compilers.
- Use `python:3.12-slim`, not `python:3.12-alpine`. Alpine uses musl
  libc which causes compatibility issues with asyncpg.

---

### Spike 4 — Async database engine and session factory

**Status**: ☐ Not started

**Depends on**: Spike 2 (settings must exist to read DATABASE_URL)

**Goal**:
Set up the SQLAlchemy async engine, session factory, and Alembic
migration tooling that all domain models and database operations
depend on.

**Context**:
We use SQLAlchemy's async engine because FastAPI is an async framework.
Using the sync engine inside async route handlers would block the event
loop and destroy performance under concurrent requests.

`get_db_session` is an async generator used as a FastAPI dependency.
FastAPI calls it before each request, yields a database session into
the route handler, and closes the session cleanly after the response —
even if an exception occurred.

Alembic handles schema migrations. When a model changes, the developer runs:
  1. `alembic revision --autogenerate -m "description"` — generates the file
  2. `alembic upgrade head` — applies it to the database

Alembic's `env.py` runs synchronously by design and needs a special
async wrapper to work with our async engine.

**Files to create**:
- `app/core/database.py`
- `alembic/` directory with `env.py` and `alembic.ini`

**Acceptance Criteria**:
- [ ] `app/core/database.py` exists with:
        - `engine` via `create_async_engine(settings.DATABASE_URL)`
        - `AsyncSessionLocal` via `async_sessionmaker(engine, class_=AsyncSession)`
        - `get_db_session` async generator that:
            - yields an `AsyncSession`
            - commits on success
            - rolls back on exception
            - always closes the session after the request

- [ ] `alembic/` initialised with async support:
        - `alembic.ini` points to `alembic/versions/`
        - `alembic/env.py` uses `run_async_migrations()` pattern
        - `alembic/env.py` imports SQLModel metadata for autogenerate

- [ ] These commands run without errors against a running PostgreSQL:
        alembic revision --autogenerate -m "init"
        alembic upgrade head
        alembic downgrade -1

- [ ] `get_db_session` closes the session cleanly even when
      an exception is raised inside the route handler

**Notes**:
- Use `create_async_engine`, not `create_engine`
- Use `AsyncSession`, not `Session`
- Use `async_sessionmaker`, not `sessionmaker`
- Import metadata for Alembic like this:
    from sqlmodel import SQLModel
    target_metadata = SQLModel.metadata
- Async pattern for Alembic env.py:
    async def run_async_migrations():
        async with engine.begin() as conn:
            await conn.run_sync(do_run_migrations)

---

### Spike 5 — FastAPI application factory and health check

**Status**: ☐ Not started

**Depends on**: Spike 2 (settings), Spike 4 (database session)

**Goal**:
Create the FastAPI app instance with lifespan management, middleware,
and a health check endpoint that actively verifies all infrastructure
connections are alive.

**Context**:
`main.py` is the entry point of the application. It creates the FastAPI
app, registers all domain routers, and configures middleware. We use the
lifespan context manager for startup and shutdown — the older
`@app.on_event` approach is deprecated in FastAPI.

The `/health` endpoint is the "done" signal for this spike. It actively
checks that the database and Redis are reachable — not just that the
app process started. This endpoint is used for docker-compose health
checks and future deployment readiness probes.

**File to create**: `app/main.py`

**Acceptance Criteria**:
- [ ] `app/main.py` exists with:
        - FastAPI app created inside `create_application() -> FastAPI`
        - Lifespan context manager registered on the app
        - CORS middleware configured from `settings`
        - A clearly commented section where domain routers are registered

- [ ] `GET /health` returns HTTP 200 with:
        {
            "status": "ok",
            "database": "ok",
            "redis": "ok"
        }

- [ ] Health check actively verifies connections:
        - Executes `SELECT 1` against the database
        - Executes `PING` against Redis
        - If any service fails, its value becomes "error" not "ok"
        - The endpoint never returns HTTP 500 — all exceptions are
          caught internally and reported in the response body

- [ ] `uvicorn app.main:app --reload` starts with no errors
- [ ] `GET /health` returns 200 with all services "ok" when
      all docker-compose services are running

**Notes**:
- Use `@asynccontextmanager` lifespan, not `@app.on_event("startup")`
- Keep `main.py` thin — no business logic belongs here
- CORS origins must come from `settings`, never hardcoded
- The health check opens its own lightweight connection rather than
  using `get_db_session`, to avoid masking session factory issues

---

## 7. Known Blind Spots (Flagged Early)

| # | Blind Spot | Why It Matters |
|---|---|---|
| 1 | `例假` vs `休息日` must be distinct values in the data model | Violation detection produces wrong results if treated the same |
| 2 | Cycle window start date must be admin-configurable | Without it, 雙週/四週/八週 violation detection cannot evaluate windows correctly |
| 3 | Employee preferences need explicit hard/soft distinction | The optimizer cannot function correctly without knowing which constraints are negotiable |
| 4 | 11-hour shift-change rule (Article 34) is separate from 變形工時 rules | Easy to miss — must be in the violation engine from the start |
| 5 | Special employee categories have stricter limits | Pregnant employees, under-18s etc. have different overtime caps under 勞基法 |
| 6 | Leave type complexity — each type has different pay/accumulation rules | Simple at launch, becomes complex when quota enforcement is added |
| 7 | Audit trail is a legal requirement | Employers must prove schedule compliance to 勞動局 — no soft deletes on schedule records |
| 8 | `organization_id` on every domain table | Required for future shared deployment — never skip it |

---

## 8. Open / TBD Items

| Item | Status | Blocking? |
|---|---|---|
| Schedule generation input format (date range, period definition) | TBD | Blocks Phase 2 schedule sprint |
| Notification delivery channel (email / LINE / in-app) | TBD | Does not block Phase 1 |
| Department feature design | TBD | Does not block Phase 1 |
| Leave quota enforcement logic | Future plan | Does not block Phase 1 |
| Schedule generation algorithm design | TBD | Blocks Phase 2 schedule sprint |
