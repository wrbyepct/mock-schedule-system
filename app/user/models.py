import enum
from typing import TYPE_CHECKING

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
        foreign_key="departments.id",
        default=None,
        nullable=True,
        ondelete="SET NULL",
    )
    department: "Department" | None = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    skill_tags: list["SkillTag"] = Relationship(
        back_populates="users",
        link_model=UserSkillTag,
        sa_relationship_kwargs={
            "lazy": "raise",
        },
    )
