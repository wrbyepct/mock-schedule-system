from __future__ import annotations

from typing import TYPE_CHECKING

from app.user.schemas import UserCreate

from .exceptions import UserExistsError

if TYPE_CHECKING:
    from app.user.repo import UserRepo


class AuthService:
    async def register(
        self,
        user_data: UserCreate,
        user_repo: UserRepo,
    ):
        user = await user_repo.get_user_by_email(user_data.email)
        if user is not None:
            raise UserExistsError()  # TODO:Add all exception handlers at once

        new_user = await user_repo.create_user(user_data)
        return new_user


async def get_auth_service():
    return AuthService()
