from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class AuthService:
    async def register(self, user_data: dict, session: AsyncSession):
        pass


auth_service = AuthService()
