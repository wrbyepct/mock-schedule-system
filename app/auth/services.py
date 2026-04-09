from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    async def register(self, user_data: dict, session: AsyncSession):
        # validate email
        # validate password
        # check user exists
        # hash
        pass


auth_service = AuthService()
