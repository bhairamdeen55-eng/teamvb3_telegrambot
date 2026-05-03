# db/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from config import settings


def _resolve_db_url() -> str:
    """
    Railway / Neon jaise providers postgres://... dete hain,
    jabki asyncpg ko postgresql+asyncpg://... chahiye.
    """
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _make_engine():
    """
    SQLite aur PostgreSQL dono handle karta hai.
    SQLite: pool_size/max_overflow support nahi karta — NullPool use karo.
    PostgreSQL: AsyncAdaptedQueuePool use hoga with pool settings.
    """
    db_url = _resolve_db_url()
    is_sqlite = "sqlite" in db_url

    if is_sqlite:
        return create_async_engine(
            db_url,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        return create_async_engine(
            db_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=False,
        )


# ── Engine & Session ──────────────────────────────────────────
engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Alias — __init__.py aur baaki files ke saath compatible
async_session_factory = AsyncSessionLocal

# ── Base Model ────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Init DB ───────────────────────────────────────────────────
async def init_db() -> None:
    """Saari tables create karo startup pe."""
    from db import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Shutdown pe engine dispose karo."""
    await engine.dispose()


# ── Session Dependency ────────────────────────────────────────
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
