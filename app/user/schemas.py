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
