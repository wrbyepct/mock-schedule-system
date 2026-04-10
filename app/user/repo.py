from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.security import hash_password
from app.shared.dependencies import Session
from app.user.models import User

from .schemas import UserCreate


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate):

        new_user = User(
            **user_data.model_dump(exclude={"password"}),
            password_hash=hash_password(user_data.password),
        )

        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def get_user_by_email(self, email: str):
        statement = select(User).where(col(User.email) == email)
        result = await self.session.exec(statement)
        return result.one_or_none()


async def get_user_repo(session: Session):
    return UserRepo(session=session)
