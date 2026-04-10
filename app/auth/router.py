from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.user.repo import UserRepo, get_user_repo
from app.user.schemas import UserCreate, UserPublic

from .services import AuthService, get_auth_service

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    user_repo: Annotated[UserRepo, Depends(get_user_repo)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    new_user = await auth_service.register(user_data, user_repo)
    return new_user
