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
