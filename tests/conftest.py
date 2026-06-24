"""Test harness: in-process app over a fresh sqlite database, Gemini mocked.

Schema is created with ``Base.metadata.create_all`` (not Alembic) for speed.
"""

import os
from collections.abc import AsyncIterator

import pytest_asyncio

# Configure environment before any app import reads settings.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ALLOWLIST_TELEGRAM_IDS", "111111111,222222222")
os.environ.setdefault("DEV_DEFAULT_TELEGRAM_ID", "111111111")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.api.dependencies.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models_registry import Base  # noqa: E402

# A single shared in-memory sqlite engine for the test session.
_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _schema() -> AsyncIterator[None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncIterator:
    async with _Session() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async def _override_db():
        async with _Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Telegram-User-Id": "111111111"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
