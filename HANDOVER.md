# Handover Document
Generated: 2026-04-10
Status: Phase 2 — Auth Layer Complete

---

## 1. Project Overview

mock-schedule-system is a general-purpose shift scheduling system designed to
auto-generate shift schedules for all company departments, fully complying with
Taiwan's 勞基法 (Labor Standards Act) and supporting all four 變形工時 (flexible
working hours) systems:

- 一例一休
- 二週變形工時
- 四週變形工時
- 八週變形工時

### What it does (v1):
- User registration and authentication (JWT + OAuth2)
- Department management
- Skill tag management per department
- Staff skill tag assignment

### What is deferred to v2:
- Department-level skill tag enforcement
- Admin-assigned skill tags with `assigned_by` and `assigned_at` audit fields
- Full shift schedule auto-generation with 勞基法 violation detection

---

## 2. Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Backend          | FastAPI (async)                         |
| ORM              | SQLModel + SQLAlchemy 2.0 (async)       |
| Database         | PostgreSQL (running in Docker)          |
| Async driver     | asyncpg                                 |
| Migrations       | Alembic (async-compatible)              |
| Package manager  | uv                                      |
| Settings         | pydantic-settings                       |
| Password hashing | pwdlib[argon2]                          |
| JWT              | PyJWT                                   |
| Linting          | ruff                                    |
| Type checking    | mypy                                    |

---

## 3. Folder Structure

```
mock-schedule-system/
├── alembic/
│   ├── env.py                             ← async-compatible Alembic config
│   └── versions/
│       └── b01eb08f2415_init.py           ← verified, applied migration
├── app/
│   ├── models.py                          ← imports all models for Alembic + SQLAlchemy registry
│   ├── main.py                            ← FastAPI app, router registration, exception handlers
│   ├── shared/
│   │   ├── models.py                      ← TimestampMixin
│   │   ├── link_table.py                  ← UserSkillTag junction table
│   │   └── dependencies.py               ← Session type alias
│   ├── core/
│   │   ├── config.py                      ← pydantic-settings Settings singleton
│   │   ├── database.py                    ← async engine + session factory
│   │   └── security.py                    ← password hashing, JWT create/decode
│   ├── auth/
│   │   ├── router.py                      ← POST /auth/register/
│   │   ├── services.py                    ← AuthService class
│   │   └── exceptions.py                  ← UserExistsError + global handler registration
│   ├── department/
│   │   └── models.py                      ← Department model
│   ├── skill_tag/
│   │   └── models.py                      ← SkillTag model
│   └── user/
│       ├── models.py                      ← User model + UserRole enum
│       ├── schemas.py                     ← UserBase, UserCreate, UserPublic
│       └── repo.py                        ← UserRepo class
```

---

## 4. All Design Decisions & Reasoning

### 4.1 table=True vs table=False
`table=True` creates actual DB tables. `table=False` is pure Pydantic — for
schemas only. Rule: never return a `table=True` model directly as a
`response_model`. Always use a separate Pydantic schema.

### 4.2 Hybrid primary key (id + uid)
- `id` (int) — internal only, used for DB joins. Fast.
- `uid` (UUID) — exposed in API responses. Not guessable, prevents enumeration attacks.
- Foreign keys always reference `id`, never `uid`.

### 4.3 UserRole as str + Enum
`class UserRole(str, enum.Enum)` — stored as plain string in DB, enforced by
Pydantic at API boundary. Three roles: `superuser`, `admin`, `staff`. Default is `staff`.

### 4.4 Skill tags design
- `SkillTag` — admin-configured options per department (the menu).
- `UserSkillTag` — junction table recording which staff selected which tags (the order).
- Explicit junction model chosen over SQLAlchemy `link_model` because v2 will add `assigned_by` and `assigned_at` fields.
- `UserSkillTag` lives in `app/shared/link_table.py` to avoid circular imports.

### 4.5 department_id on User is nullable
Department assignment is a v1 placeholder — not enforced yet.
`ondelete="SET NULL"` — deleting a department does NOT delete users, it nulls their `department_id`.

### 4.6 department_id on SkillTag is NOT nullable
A skill tag without a department makes no domain sense.
`ondelete="CASCADE"` — deleting a department deletes all its skill tags, which cascades to `UserSkillTag`.

### 4.7 lazy="raise" on all relationships
Prevents accidental N+1 queries. Forces explicit loading via `selectinload` or
`joinedload` in every query.

### 4.8 sa_column_kwargs over sa_column in TimestampMixin
Shared `Column()` objects in mixins cause SQLModel bugs when inherited by
multiple tables. `sa_column_kwargs={}` is the safe pattern.

### 4.9 Alembic async pattern
Alembic's `env.py` runs synchronously by default. Requires
`asyncio.run(run_async_migrations())` wrapper. All models must be imported in
`app/models.py` so `SQLModel.metadata` is populated before autogenerate runs.

### 4.10 ondelete vs cascade placement
- `ondelete="CASCADE"` belongs on the FK field — talks to PostgreSQL directly.
- `cascade="all, delete-orphan"` belongs on the Relationship — talks to SQLAlchemy ORM.
- Both are needed: ORM cascade for Python-level deletes, DB cascade as safety net for direct SQL deletes.

### 4.11 Schema separation from DB models
API schemas (`UserBase`, `UserCreate`, `UserPublic`) inherit from `BaseModel`,
not `SQLModel`. DB models and API schemas never share a base class — they serve
different masters and diverge over time.

`UserPublic` has `model_config = {"from_attributes": True}` to allow
`model_validate()` on ORM objects. `UserCreate` does not need it.

### 4.12 role not in UserCreate
Self-service registration must never allow clients to assign their own role.
`role` is hardcoded to `UserRole.staff` via the `User` model default. Role
elevation goes through a separate privileged endpoint.

### 4.13 Password hashing — pwdlib over passlib
`passlib` is unmaintained and incompatible with Python 3.13+. The official
FastAPI docs have migrated to `pwdlib`. `PasswordHash.recommended()` uses
Argon2 by default — the IETF-recommended algorithm and winner of the Password
Hashing Competition.

### 4.14 JWT design
- `sub` — stores `uid` (string). Not `id` (prevents DB integer leakage) and not `email` (can change).
- `exp` — PyJWT validates this automatically on `decode()`.
- `role` — included in payload to avoid a DB lookup on every request. Tradeoff: stale role if user is demoted before token expiry. Acceptable for v1.
- `tid` — unique token ID (UUID). Enables token blacklisting on logout.
- `decode_token` raises `InvalidTokenError` — catching it and converting to HTTP 401 is the router/dependency layer's responsibility.

### 4.15 Dependency injection scope
FastAPI's `Depends()` only works at route handler function signatures. It has
no awareness of class methods. `UserRepo` is injected at the router level and
passed explicitly into `AuthService.register()`. `AuthService` is stateless —
no constructor dependencies.

### 4.16 Exception handling pattern
Domain exceptions (e.g. `UserExistsError`) are raised in the service layer.
HTTP mapping happens in a global exception handler registered in `main.py` via
`app.add_exception_handler()`. The handler is defined as a static method on
the exception class itself for colocation. All exceptions are registered via
`register_all_exceptions(app)` called once in `main.py`.

### 4.17 Login uses OAuth2PasswordRequestForm
`OAuth2PasswordRequestForm` has a hardcoded `username` field — cannot be
renamed. Convention: client puts email in the `username` field. Service layer
treats `form_data.username` as email internally. This enables Swagger UI
"Authorize" button out of the box.

### 4.18 model_dump exclude syntax
`model_dump(exclude={"password"})` — must be a set, not a string. Passing a
string iterates over its characters silently.

---

## 5. Complete Model & Schema Code

### app/shared/models.py

```python
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel, table=False):
    id: int | None = Field(default=None, primary_key=True)
    uid: UUID = Field(
        default_factory=uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": False,
        },
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
            "nullable": False,
        },
    )
```

### app/shared/link_table.py

```python
from sqlmodel import Field, SQLModel


class UserSkillTag(SQLModel, table=True):
    __tablename__ = "user_skill_tags"

    user_id: int | None = Field(
        foreign_key="users.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    skill_tag_id: int | None = Field(
        foreign_key="skill_tags.id",
        primary_key=True,
        ondelete="CASCADE",
    )
```

### app/department/models.py

```python
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from app.skill_tag.models import SkillTag
    from app.user.models import User


class Department(TimestampMixin, table=True):
    __tablename__ = "departments"

    name: str = Field(nullable=False, max_length=100, unique=True, index=True)

    skill_tags: list["SkillTag"] = Relationship(
        back_populates="department",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
        },
    )

    users: list["User"] = Relationship(
        back_populates="department",
        sa_relationship_kwargs={"lazy": "raise"},
    )
```

### app/skill_tag/models.py

```python
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, UniqueConstraint

from app.shared.models import TimestampMixin
from app.shared.link_table import UserSkillTag

if TYPE_CHECKING:
    from app.department.models import Department
    from app.user.models import User


class SkillTag(TimestampMixin, table=True):
    __tablename__ = "skill_tags"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "department_id",
            name="uq_skill_name_per_department",
        ),
    )

    name: str = Field(nullable=False, max_length=100, index=True)
    description: str | None = Field(default=None, max_length=255, nullable=True)

    department_id: int | None = Field(
        default=None,
        foreign_key="departments.id",
        nullable=False,
        ondelete="CASCADE",
    )

    department: "Department" = Relationship(
        back_populates="skill_tags",
        sa_relationship_kwargs={"lazy": "raise"},
    )

    users: list["User"] = Relationship(
        back_populates="skill_tags",
        link_model=UserSkillTag,
        sa_relationship_kwargs={"lazy": "raise"},
    )
```

### app/user/models.py

```python
import enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.shared.link_table import UserSkillTag
from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from app.department.models import Department
    from app.skill_tag.models import SkillTag


class UserRole(str, enum.Enum):
    superuser = "superuser"
    admin = "admin"
    staff = "staff"


class User(TimestampMixin, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, max_length=255)
    password_hash: str = Field(exclude=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: UserRole = Field(default=UserRole.staff)
    is_active: bool = Field(default=True, nullable=False)

    department_id: int | None = Field(
        default=None,
        foreign_key="departments.id",
        nullable=True,
        ondelete="SET NULL",
    )

    department: Optional["Department"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"lazy": "raise"},
    )

    skill_tags: list["SkillTag"] = Relationship(
        back_populates="users",
        link_model=UserSkillTag,
        sa_relationship_kwargs={"lazy": "raise"},
    )
```

### app/user/schemas.py

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.user.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase):
    uid: UUID
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

### app/core/security.py

```python
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError  # noqa: F401 — re-exported for callers
from pwdlib import PasswordHash

from app.core.config import settings

pwd_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return pwd_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_hasher.verify(plain_password, hashed_password)


def create_access_token(user_uid: str, user_role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_uid,
        "exp": expire,
        "role": user_role,
        "tid": str(uuid4()),
    }
    return jwt.encode(
        payload=payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token=token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )  # InvalidTokenError must be caught at the router/dependency layer
```

### app/user/repo.py

```python
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import hash_password
from app.shared.dependencies import Session
from app.user.models import User
from app.user.schemas import UserCreate


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate) -> User:
        new_user = User(
            **user_data.model_dump(exclude={"password"}),
            password_hash=hash_password(user_data.password),
        )
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.exec(statement)
        return result.one_or_none()


async def get_user_repo(session: Session) -> UserRepo:
    return UserRepo(session=session)
```

### app/auth/exceptions.py

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class UserExistsError(Exception):
    """Raised when registration is attempted with an already registered email."""

    @staticmethod
    async def handler(request: Request, exc: "UserExistsError") -> JSONResponse:
        return JSONResponse(
            content={"detail": "An account with this email already exists."},
            status_code=status.HTTP_409_CONFLICT,
        )


all_exceptions = [UserExistsError]


def register_all_exceptions(app: FastAPI) -> None:
    for exc in all_exceptions:
        app.add_exception_handler(exc, exc.handler)
```

### app/auth/services.py

```python
from typing import TYPE_CHECKING

from app.auth.exceptions import UserExistsError
from app.user.schemas import UserCreate

if TYPE_CHECKING:
    from app.user.repo import UserRepo


class AuthService:
    async def register(self, user_data: UserCreate, user_repo: "UserRepo"):
        user = await user_repo.get_user_by_email(user_data.email)
        if user is not None:
            raise UserExistsError()
        return await user_repo.create_user(user_data)


async def get_auth_service() -> AuthService:
    return AuthService()
```

### app/auth/router.py

```python
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.services import AuthService, get_auth_service
from app.user.repo import UserRepo, get_user_repo
from app.user.schemas import UserCreate, UserPublic

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    user_repo: Annotated[UserRepo, Depends(get_user_repo)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    new_user = await auth_service.register(user_data, user_repo)
    return new_user
```

### app/models.py

```python
import app.department.models  # noqa: F401
import app.skill_tag.models   # noqa: F401
import app.user.models        # noqa: F401
```

---

## 6. What Comes Next

### Step 1 — POST /auth/login
- Uses `OAuth2PasswordRequestForm` (form data, not JSON)
- `form_data.username` is treated as email internally
- Returns `TokenResponse` schema: `{"access_token": "...", "token_type": "bearer"}`
- Service layer: verify email exists → verify password → create token
- Raises `HTTP 401` on bad credentials

### Step 2 — GET /auth/me
- Protected route — requires valid JWT
- Create `get_current_user` dependency in `app/shared/dependencies.py`
  - Extracts token from `Authorization: Bearer <token>` header
  - Decodes token, extracts `sub` (uid)
  - Fetches user from DB by uid
  - Raises `HTTP 401` if token invalid or user not found
- Returns `UserPublic`

### Step 3 — POST /auth/logout
- Requires valid JWT
- Extracts `tid` from token payload
- Adds `tid` to blacklist
- Open decision: blacklist storage — Redis or DB table? (see section 7)
- Returns `HTTP 204`

### Step 4 — GET /auth/refresh
- Accepts refresh token
- Validates it, extracts `sub`
- Issues new access + refresh token pair
- Open decision: refresh token strategy (see section 7)

### Step 5 — Department CRUD
- `POST /departments/` — create
- `GET /departments/` — list
- `GET /departments/{uid}` — get by uid
- `PATCH /departments/{uid}` — update
- `DELETE /departments/{uid}` — delete

### Step 6 — Skill Tag CRUD
- Same pattern as department
- Scoped under department: `POST /departments/{uid}/skill-tags/`

### Step 7 — User Skill Tag Assignment
- `POST /users/{uid}/skill-tags/` — assign tag to user
- `DELETE /users/{uid}/skill-tags/{tag_uid}` — remove tag from user

---

## 7. Open Decisions

These must be answered before implementing the relevant steps.

### Token blacklist storage (needed for logout)
- **Option A**: Redis — fast, TTL-native, expires automatically with token
- **Option B**: DB table — simpler, no extra infrastructure, but grows unbounded
- Recommendation: Redis if Redis is already in the stack for Celery; DB table otherwise for v1 simplicity

### Refresh token strategy (needed for refresh endpoint)
- **Option A**: Refresh token as JWT — stateless, but can't be revoked
- **Option B**: Refresh token as opaque string stored in DB — revocable, but requires DB lookup on every refresh
- Decision needed before Step 4

### Role-based route guards
- Will protected routes check role from JWT payload or re-fetch from DB?
- JWT payload is faster but can be stale if role changes before expiry
- DB fetch is always fresh but costs a query

### Response envelope
- Bare objects: `{"uid": "...", "email": "..."}`
- Wrapped: `{"data": {"uid": "...", "email": "..."}, "message": "success"}`
- Must be decided before Department CRUD to establish the pattern consistently

---

## 8. Known Gotchas

| Bug / Quirk | Detail |
|---|---|
| `func` import | Must come from `sqlalchemy`, not `sqlmodel`. `from sqlmodel import func` raises `ImportError` |
| `onupdate=True` | Silently does nothing. Must be `onupdate=func.now()` |
| `table=True` on mixin | Setting `table=True` on `TimestampMixin` creates a real DB table. Must be `table=False` |
| `sa_column` in mixins | Shared `Column()` objects across tables cause bugs. Use `sa_column_kwargs={}` instead |
| `department_id` nullable in migration | SQLModel sometimes ignores `nullable=False` on FK fields. Always manually verify the generated migration |
| `lazy="raise"` | Every query that accesses a relationship must explicitly load it. Forgetting causes a `MissingGreenlet` error at runtime |
| `back_populates` typo | Must exactly match the attribute name on the other model. SQLAlchemy raises a cryptic error at startup if mismatched |
| `cascade` string format | Must be `"all, delete-orphan"` with a comma. `"all delete-orphan"` silently ignores `delete-orphan` |
| Alembic model detection | All models must be imported in `app/models.py`. Missing imports = Alembic silently skips that table |
| `ondelete` placement | Belongs on the FK field, not the Relationship. The relationship handles ORM-level cascade, the FK field handles DB-level cascade |
| `from __future__ import annotations` | Breaks SQLAlchemy relationship resolution in model files. Do not add to any file containing `table=True` models |
| `Depends()` in class methods | FastAPI DI only works at route handler signatures. Never place `Depends()` inside service or repo methods |
| `model_dump(exclude=...)` | Must be a set: `exclude={"password"}`. A string silently iterates over its characters |
| `timedelta` positional arg | First positional arg is `days`, not `minutes`. Always use `timedelta(minutes=...)` explicitly |
| `dict[str, any]` | Lowercase `any` is a Python built-in function, not a type. Use `Any` from `typing` |
| `pwdlib` over `passlib` | `passlib` is unmaintained and breaks on Python 3.13+. Use `pwdlib[argon2]` |
| `department.users` no cascade | Intentional — deleting a department must NOT delete users. Only nulls their `department_id` via `SET NULL` |
