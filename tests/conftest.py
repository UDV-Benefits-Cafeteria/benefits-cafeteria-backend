from datetime import date
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.v1.dependencies import get_current_user
from src.db.db import AsyncSession, async_session_factory, engine
from src.main import app
from src.models import User
from src.models.base import Base
from src.models.users import UserRole
from src.schemas.user import UserRead

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session", autouse=True)
async def setup_db_schema() -> None:
    """
    Creates the test database schema before any tests and drops it afterward.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Provides a transactional database session for tests. Rolls back after each test.
    """
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
async def test_admin_user(db_session: AsyncSession) -> User:
    """
    Adds a default admin user for testing.
    """
    admin_user = User(
        id=199,
        email="admin@example.com",
        firstname="Admin",
        lastname="User",
        middlename=None,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        legal_entity_id=None,
        position_id=None,
        image_url=None,
        password="qwertyuiop123",
    )
    db_session.add(admin_user)
    await db_session.commit()
    return admin_user


@pytest.fixture(scope="session")
async def test_hr_user(db_session: AsyncSession) -> User:
    """
    Adds a default hr user for testing.
    """
    hr_user = User(
        id=199,
        email="admin@example.com",
        firstname="HR",
        lastname="User",
        middlename=None,
        role=UserRole.HR,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        legal_entity_id=None,
        position_id=None,
        image_url=None,
        password="qwertyuiop123",
    )
    db_session.add(hr_user)
    await db_session.commit()
    return hr_user


@pytest.fixture(scope="session")
async def async_test_admin_client(
    test_admin_user: User, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an AsyncClient instance for testing with FastAPI for admin role.
    Overrides the user dependency for authenticated requests.
    """

    # Override the `get_current_user` dependency to return `test_admin_user`
    async def override_get_current_user():
        return UserRead.model_validate(test_admin_user)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    # Clear the dependency overrides after tests
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def async_test_hr_client(
    test_hr_user: User, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an AsyncClient instance for testing with FastAPI for hr role.
    Overrides the user dependency for authenticated requests.
    """

    # Override the `get_current_user` dependency to return `test_admin_user`
    async def override_get_current_user():
        return UserRead.model_validate(test_hr_user)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    # Clear the dependency overrides after tests
    app.dependency_overrides.clear()
