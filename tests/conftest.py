"""Shared test fixtures.

Tests run against an in-memory SQLite DB to keep CI hermetic. The app
engine is monkey-patched to a fresh per-test SQLite engine, and
`Base.metadata.create_all` substitutes for migrations in tests.
"""
import os
import sys
from collections.abc import AsyncGenerator

# Set required env vars before importing app code.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import database as db_module
from app.core.db.base import Base


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine, session_factory, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "async_session", session_factory)

    # Reload main so the FastAPI app picks up the patched session factory
    # via its dependencies (which import lazily through db_module).
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    from app.main import app  # noqa: WPS433 — late import is intentional

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
