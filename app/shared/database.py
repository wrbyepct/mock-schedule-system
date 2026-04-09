from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel import text

from app.shared.config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 'hello"))
        print("DB connects successfully")
    except Exception:
        print("Failed connects to db: {e}")
