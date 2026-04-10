from sqlmodel import Field, SQLModel


class UserSkillTag(SQLModel, table=True):
    """User and Skill Tag M-2-M jointable"""

    __tablename__ = "user_skill_tags"
    # Composite primary key makes record unique
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
