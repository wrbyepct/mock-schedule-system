from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.session import AsyncSession


class AuthService:
    async def reigster(self, user_data: dict, session: AsyncSession):
        # prerequisite: validate email
        # prerequisite: validate password
        # check email already registered
        # hash passsword
        # add user
        pass


auth_service = AuthService()
