from fastapi import APIRouter, status

from app.shared.dependencies import Session

from .services import auth_service

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: dict, session: Session):
    new_user = auth_service.reigster(user_data=user_data, session=session)
    return new_user
