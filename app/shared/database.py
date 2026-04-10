from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.shared.config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.execute((text("SELECT 'hello'")))
        print("DB connect successfully")
    except Exception as e:
        print(f"Failed to connect db: {e}")
