import enum


class UserRole(str, enum.Enum):
    superuser = "superuser"
    admin = "admin"
    staff = "staff"


class UserSkillTag:
    pass
