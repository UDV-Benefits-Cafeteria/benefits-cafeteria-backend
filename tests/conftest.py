# tests/conftest.py
import asyncio
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings
from src.db.db import Base, get_async_session
from src.main import app

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(_env_prefix="TEST_")


@pytest.fixture(scope="session")
def engine_test(test_settings: Settings):
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=True,
    )
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="session")
def async_session_factory(engine_test) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine_test, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture(scope="function")
async def async_session(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="session")
def override_get_async_session(async_session_factory: async_sessionmaker[AsyncSession]):
    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = _override_get_async_session
    yield
    app.dependency_overrides.pop(get_async_session, None)


@pytest.fixture(scope="session", autouse=True)
async def prepare_database(engine_test):
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
