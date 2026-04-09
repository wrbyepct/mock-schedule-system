import enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.skill_tag.models import SkillTag


class UserRole(str, enum.Enum):
    superuser = "superuser"
    admin = "admin"
    staff = "staff"


class User:
    pass


class UserSkillTag(SQLModel, table=True):
    """Link model for SkillTag and User."""

    user_id: int = Field(
        foreign_key="users.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    skill_tag_id: int = Field(
        foreign_key="skill_tags.id", primary_key=True, ondelete="CASCADE"
    )

    user: "User" = Relationship(back_populates="skill_tags")
    skill_tag: "SkillTag" = Relationship(back_populates="users")

    # For v2 to add more field if needed
