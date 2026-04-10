from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, UniqueConstraint

from app.shared.models import TimestampMixin
from app.user.models import UserSkillTag

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
    department_id: int | None = Field(
        default=None, foreign_key="departments.id", ondelete="CASCADE"
    )

    department: Optional["Department"] = Relationship(
        back_populates="skill_tags",
        sa_relationship_kwargs={
            "lazy": "raise",
        },
    )

    users: list["User"] = Relationship(
        back_populates="skill_tags",
        link_model=UserSkillTag,
        sa_relationship_kwargs={
            "lazy": "raise",
        },
    )
