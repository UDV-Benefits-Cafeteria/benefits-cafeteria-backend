import asyncio
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.db.db import Base, engine
from src.main import app

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """
    Set up the test database for the entire test session.

    This fixture creates the database schema before any tests run and
    drops it after all tests are completed. It uses an async context
    manager to ensure that the database operations are handled properly.

    The database schema is created by running the metadata of the
    Base model.

    Yields:
        None: This fixture does not return any value.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await asyncio.sleep(0)  # Ensure async operations complete
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing.

    This fixture sets up an AsyncClient using httpx with ASGITransport
    to communicate with the FastAPI app. The base URL is set for the
    API version being tested.

    Yields:
        AsyncClient: An instance of AsyncClient for making requests
        to the FastAPI application during tests.
    """
    transport = ASGITransport(app)
    async with AsyncClient(
        transport=transport, base_url="http://test/api/v1"
    ) as client:
        yield client
