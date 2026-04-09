from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, UniqueConstraint

from app.shared.models import TimestampMixin

if TYPE_CHECKING:
    from app.department.models import Department
    from app.user.models import UserSkillTag


class SkillTag(TimestampMixin, table=True):
    __tablename__ = "skill_tags"
    __table_args__ = (
        UniqueConstraint("name", "department_id", name="uq_skill_tag_name_department"),
    )

    name: str = Field(nullable=False, max_length=100, index=True)
    description: str | None = Field(nullable=True, max_length=255, default=None)

    department_id: int | None = Field(
        default=None, foreign_key="department.id", ondelete="CASCADE"
    )

    department: "Department" = Relationship(
        back_populates="skill_tags",
        sa_relationship_kwargs={"lazy": "raise"},
    )

    user_skill_tags: list["UserSkillTag"] = Relationship(
        back_populates="skill_tag",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
        },
    )
