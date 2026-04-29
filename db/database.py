# db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from config import settings
from loguru import logger

class Base(DeclarativeBase):
    pass

engine: AsyncEngine = None
async_session_factory: async_sessionmaker[AsyncSession] = None

async def init_db() -> None:
    global engine, async_session_factory
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized | URL: %s", settings.db_uri_safe)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def close_db() -> None:
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")
