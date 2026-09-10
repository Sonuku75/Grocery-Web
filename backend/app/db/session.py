"""
Cartify Database Engine & Session Management (Module 0)

Features:
- Dual SQLAlchemy 2.0 Async Engines (Primary for Writes, Replica for Reads)
- Production-tuned connection pool settings (size, overflow, recycle, pre-ping)
- Lightweight, timeout-bounded health check probes
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

logger = logging.getLogger("cartify.db")

# Primary Engine (Writes, Transactions, Row Locks)
engine_primary = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Replica Engine (Read-Only Offload)
engine_replica = create_async_engine(
    settings.DATABASE_REPLICA_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a write-capable session connected to PostgreSQL Primary."""
    async with AsyncSessionPrimary() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def get_db_reader() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a read-only session connected to PostgreSQL Read Replica."""
    async with AsyncSessionReplica() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def ping_databases() -> Dict[str, bool]:
    """
    Lightweight health check probe for primary and replica databases.
    Enforces a strict 1.5s timeout to prevent health probes from hanging.
    """
    results = {"primary": False, "replica": False}

    async def _probe_primary():
        async with AsyncSessionPrimary() as session:
            await session.execute(text("SELECT 1"))

    async def _probe_replica():
        async with AsyncSessionReplica() as session:
            await session.execute(text("SELECT 1"))

    try:
        await asyncio.wait_for(_probe_primary(), timeout=1.5)
        results["primary"] = True
    except Exception as e:
        logger.debug(f"Primary DB probe failed: {e}")

    try:
        await asyncio.wait_for(_probe_replica(), timeout=1.5)
        results["replica"] = True
    except Exception as e:
        logger.debug(f"Replica DB probe failed: {e}")

    return results
