from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from app.skill_tag.models import SkillTag
    from app.user.models import User


class Department(TimestampMixin, table=True):
    __tablename__ = "departments"

    name: str = Field(default="我的部門", max_length=100, unique=True, index=True)

    # system level skill tags
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
    )  # TODO: Test department deleted, users are intact
