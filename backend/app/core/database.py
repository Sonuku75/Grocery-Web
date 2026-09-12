from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Primary DB Engine: For Writes, Transactions, and Pessimistic Locks
engine_primary = create_async_engine(
    settings.DATABASE_PRIMARY_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Read Replica DB Engine: For Read-Heavy Catalog & Search Queries
engine_replica = create_async_engine(
    settings.DATABASE_REPLICA_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Session factories
AsyncSessionPrimary = async_sessionmaker(
    bind=engine_primary,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AsyncSessionReplica = async_sessionmaker(
    bind=engine_replica,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db_writer() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional database session pointing to PostgreSQL Primary."""
    async with AsyncSessionPrimary() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

get_db = get_db_writer

async def get_db_reader() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-only database session pointing to PostgreSQL Read Replica."""
    async with AsyncSessionReplica() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def ping_databases() -> dict:
    """Health check ping for primary and replica pools."""
    from sqlalchemy import text
    results = {"primary": False, "replica": False}
    try:
        async with AsyncSessionPrimary() as s:
            await s.execute(text("SELECT 1"))
            results["primary"] = True
    except Exception as e:
        results["primary_error"] = str(e)

    try:
        async with AsyncSessionReplica() as s:
            await s.execute(text("SELECT 1"))
            results["replica"] = True
    except Exception as e:
        results["replica_error"] = str(e)

    return results
