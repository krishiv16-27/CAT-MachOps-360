"""
Async SQLAlchemy engine + session factory.
Supports PostgreSQL (primary) and SQLite (demo fallback).
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
from .config import settings
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _build_engine():
    url = settings.effective_database_url
    if settings.use_sqlite:
        # SQLite needs special pool config for async
        return create_async_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.is_development,
        )
    return create_async_engine(
        url,
        pool_size=10,
        max_overflow=20,
        echo=settings.is_development,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (used in development / demo mode)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")


async def drop_db():
    """Drop all tables — for testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
