from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from app.skill_tag.models import SkillTag


class Department(TimestampMixin, table=True):
    __tablename__ = "departments"
    name: str = Field(
        nullable=False,
        max_length=100,
        unique=True,
        index=True,
    )
    skill_tags: list["SkillTag"] = Relationship(
        back_populates="department",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
        },
    )
