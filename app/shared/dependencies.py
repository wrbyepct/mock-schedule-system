from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.shared.database import get_db

Session = Annotated[AsyncSession, Depends(get_db)]
