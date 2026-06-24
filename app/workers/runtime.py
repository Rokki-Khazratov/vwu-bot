"""Async runtime for Celery tasks.

Celery tasks are synchronous; our stack is async. Each task runs its coroutine
with ``run()`` over a worker-scoped session. The session factory is overridable
so tests can point tasks at the in-memory test database (Celery eager mode).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_factory: async_sessionmaker[AsyncSession] | None = None


def _default_factory() -> async_sessionmaker[AsyncSession]:
    global _factory
    if _factory is None:
        engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
        _factory = async_sessionmaker(engine, expire_on_commit=False)
    return _factory


def set_session_factory(factory: async_sessionmaker[AsyncSession] | None) -> None:
    """Override the worker session factory (tests)."""
    global _factory
    _factory = factory


@asynccontextmanager
async def worker_session() -> AsyncIterator[AsyncSession]:
    async with _default_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def run[T](coro: Awaitable[T]) -> T:
    """Run a coroutine to completion from a synchronous Celery task."""
    return asyncio.run(coro)
