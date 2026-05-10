"""Async SQLAlchemy engine, session factory, and FastAPI dependencies.

The engine is a process-wide connection pool created once at import time.
Each request grabs a session via the `get_db` / `get_db_transactional`
dependencies; sessions are short-lived units-of-work, not the pool itself.

Models live elsewhere; only re-export `Base` here for convenience.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.db.base import Base

__all__ = ["Base", "engine", "async_session", "get_db", "get_db_transactional", "dispose_engine"]


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        str(settings.database_url),
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_pre_ping=True,
        future=True,
    )


engine: AsyncEngine = _build_engine()

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session that the caller must commit explicitly.

    Use when the route reads only, or when the route owns multiple
    write boundaries that should not be wrapped in one transaction.
    """
    async with async_session() as session:
        yield session


async def get_db_transactional() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session wrapped in a transaction.

    Commits on clean exit, rolls back on any exception. Prefer this for
    write routes so callers can't forget to commit.
    """
    async with async_session() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            # session.begin() already rolled back; re-raise so FastAPI
            # exception handlers can map it to a response.
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Transactional session for non-FastAPI callers (jobs, CLIs, tests)."""
    async with async_session() as session:
        async with session.begin():
            yield session


async def dispose_engine() -> None:
    """Close all pooled connections. Call on application shutdown."""
    await engine.dispose()
