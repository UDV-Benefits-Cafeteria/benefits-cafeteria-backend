from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.v1.dependencies import get_current_user
from src.config import get_settings
from src.db.db import AsyncSession, async_session_factory, engine
from src.main import app
from src.models import Category, LegalEntity, User
from src.models.base import Base
from src.models.users import UserRole
from src.schemas.user import UserRead
from src.services.sessions import SessionsService

pytest_plugins = ["pytest_asyncio"]

settings = get_settings()


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
async def admin_user(db_session: AsyncSession) -> User:
    """Create a default admin user for testing."""
    admin = User(
        id=1,
        email="admin@example.com",
        firstname="Admin",
        lastname="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        password="qwertyuiop123",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture(scope="session")
async def legal_entity1a(db_session: AsyncSession):
    """Create the first legal entity for testing."""
    entity = LegalEntity(
        id=1,
        name="Legal Entity 1a",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest.fixture(scope="session")
async def legal_entity2b(db_session: AsyncSession):
    """Create the second legal entity for testing."""
    entity = LegalEntity(
        id=2,
        name="Legal Entity 2b",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest.fixture(scope="session")
async def hr_user1(db_session: AsyncSession, legal_entity1a) -> User:
    """Create the first HR user with legal_entity_id=1."""
    legal_entity = await legal_entity1a

    hr1 = User(
        id=2,
        email="hr1@example.com",
        firstname="HR1",
        lastname="User",
        role=UserRole.HR,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        password="qwertyuiop123",
        legal_entity_id=legal_entity.id,
    )
    db_session.add(hr1)
    await db_session.commit()
    await db_session.refresh(hr1)
    return hr1


@pytest.fixture(scope="session")
async def hr_user2(db_session: AsyncSession, legal_entity2b) -> User:
    """Create the second HR user with legal_entity_id=2."""
    legal_entity = await legal_entity2b

    hr2 = User(
        id=3,
        email="hr2@example.com",
        firstname="HR2",
        lastname="User",
        role=UserRole.HR,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        password="qwertyuiop123",
        legal_entity_id=legal_entity.id,
    )
    db_session.add(hr2)
    await db_session.commit()
    await db_session.refresh(hr2)
    return hr2


@pytest.fixture(scope="session")
async def employee_user(db_session: AsyncSession) -> User:
    """Create a regular employee user with legal_entity_id=1."""
    user = User(
        id=4,
        email="user@example.com",
        firstname="Employee",
        lastname="User",
        role=UserRole.EMPLOYEE,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=200,
        password="qwertyuiop123",
        legal_entity_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_client(admin_user: User):
    """Provide an AsyncClient with admin user authentication."""

    async def override_get_current_user():
        return UserRead.model_validate(admin_user)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
async def hr_client1(hr_user1: User):
    """Provide an AsyncClient with hr_user1 authentication."""

    async def override_get_current_user():
        return UserRead.model_validate(hr_user1)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
async def hr_client2(hr_user2: User):
    """Provide an AsyncClient with hr_user2 authentication."""

    async def override_get_current_user():
        return UserRead.model_validate(hr_user2)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
async def employee_client(employee_user: User):
    """Provide an AsyncClient with regular employee user authentication."""

    async def override_get_current_user():
        return UserRead.model_validate(employee_user)

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
async def auth_client():
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def category(db_session: AsyncSession):
    """Create a category for testing."""
    category = Category(
        id=1,
        name="Test Category",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


async def get_employee_client(user_id: int):
    sessions_service = SessionsService()
    session_id = await sessions_service.create_session(
        user_id, settings.SESSION_EXPIRE_TIME
    )
    csrf_token = await sessions_service.get_csrf_token(session_id)

    client = AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test/api/v1",
        cookies={
            settings.SESSION_COOKIE_NAME: session_id,
            settings.CSRF_COOKIE_NAME: csrf_token,
        },
    )
    return client
