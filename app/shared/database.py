from sqlalchemy.ext.asyncio import create_async_engine
from .config import settings

# Engine
engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DEBUG,  # for sql query logging, debugging purposes
    pool_pre_ping=True,  # for handling stale connections, especially in production environments
    pool_recycle=3600,  # recycle connections after 1 hour to prevent timeouts
)

# Session
