from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

Session = Annotated[AsyncSession, Depends(get_db)]
