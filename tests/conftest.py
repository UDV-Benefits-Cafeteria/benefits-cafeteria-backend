from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

import src.schemas.user as user_schemas
from src.api.v1.dependencies import get_current_user
from src.config import get_settings
from src.db.db import AsyncSession, async_session_factory, engine
from src.main import app
from src.models import Benefit, BenefitRequest, Category, LegalEntity, User
from src.models.base import Base
from src.services.sessions import SessionsService
from src.utils.elastic_index import SearchService
from src.utils.email_sender.base import fm

pytest_plugins = ["pytest_asyncio"]

settings = get_settings()


@pytest.fixture(scope="session")
async def setup_db_schema() -> None:
    """
    Creates the test database schema before any tests and drops it afterward.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
async def clean_db(setup_db_schema, db_session) -> None:
    """
    Provides clean database before any tests with all the tables and their structure provided by setup_db_schema fixture
    """
    for table in reversed(
        Base.metadata.sorted_tables
    ):  # Reverse the order to avoid foreign key constraints
        await db_session.execute(table.delete())


@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Provides a database session for tests.
    """
    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create a default admin user for testing."""
    admin = User(
        id=111,
        email="admin@example.com",
        firstname="Admin",
        lastname="User",
        role=user_schemas.UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
async def category(db_session: AsyncSession):
    """Create a category for testing."""
    category = Category(
        id=111,
        name="Test Category",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture(scope="function")
async def legal_entity1a(db_session: AsyncSession) -> LegalEntity:
    """Create the first legal entity for testing."""
    entity = LegalEntity(
        id=111,
        name="Legal Entity 1a",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest.fixture(scope="function")
async def legal_entity2b(db_session: AsyncSession) -> LegalEntity:
    """Create the second legal entity for testing."""
    entity = LegalEntity(
        id=222,
        name="Legal Entity 2b",
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest.fixture(scope="function")
async def hr_user(db_session: AsyncSession, legal_entity1a) -> User:
    """Create an HR user with legal_entity_id=111."""

    hr1 = User(
        id=222,
        email="hr1@example.com",
        firstname="HRone",
        lastname="User",
        role=user_schemas.UserRole.HR,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=0,
        legal_entity_id=111,
    )
    db_session.add(hr1)
    await db_session.commit()
    await db_session.refresh(hr1)
    return hr1


@pytest.fixture(scope="function")
async def legal_entity2b_user(db_session: AsyncSession, legal_entity2b) -> User:
    """Create a regular employee user with legal_entity_id=222."""
    user = User(
        id=333,
        email="user2b@example.com",
        firstname="Employee",
        lastname="User",
        role=user_schemas.UserRole.EMPLOYEE,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=500,
        legal_entity_id=222,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def employee_user(db_session: AsyncSession, legal_entity1a) -> User:
    """Create a regular employee user with legal_entity_id=111."""
    user = User(
        id=444,
        email="user@example.com",
        firstname="Employee",
        lastname="User",
        role=user_schemas.UserRole.EMPLOYEE,
        is_active=True,
        is_verified=True,
        is_adapted=True,
        hired_at=date.today(),
        coins=200,
        legal_entity_id=111,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def benefit_requests(
    db_session: AsyncSession,
    hr_user: User,
    legal_entity2b_user: User,
    legal_entity1a,
    legal_entity2b,
) -> list[BenefitRequest]:
    """Provide 4 requests with different 'status', 'user_id' and 'created_at' fields"""
    benefit_data = [
        {"status": "pending", "user_id": 222, "created_at": date(2024, 1, 1)},
        {"status": "approved", "user_id": 222, "created_at": date(2024, 2, 1)},
        {"status": "declined", "user_id": 333, "created_at": date(2024, 3, 1)},
        {"status": "pending", "user_id": 333, "created_at": date(2024, 4, 1)},
    ]

    created_requests = []
    for data in benefit_data:
        benefit_request = BenefitRequest(**data)
        db_session.add(benefit_request)
        await db_session.commit()
        await db_session.refresh(benefit_request)
        created_requests.append(benefit_request)

    return created_requests


@pytest.fixture(scope="function")
async def benefit_request(
    db_session: AsyncSession,
    employee_user: User,
    legal_entity2b_user: User,
    request,
    clean_db,
) -> BenefitRequest:
    """Provide a benefit request with 'status' and 'user_id' passed from 'request_with_status' marker."""
    marker = request.node.get_closest_marker("request_with_status")
    if marker is None:
        raise ValueError("Marker 'request_with_status' is required")

    status = marker.args[0]
    user_id = marker.args[1]

    if user_id not in [333, 444]:
        raise ValueError(f"Invalid user_id: {user_id}. Valid values are 333 or 444.")

    benefit: Benefit = Benefit(name="Benefit123", coins_cost=0, min_level_cost=0)
    db_session.add(benefit)
    await db_session.commit()
    await db_session.refresh(benefit)

    benefit_request: BenefitRequest = BenefitRequest(
        benefit_id=benefit.id, status=status, user_id=user_id, created_at=date.today()
    )

    db_session.add(benefit_request)
    await db_session.commit()
    await db_session.refresh(benefit_request)

    return benefit_request


@pytest.fixture
async def admin_client(admin_user: User):
    """Provide an AsyncClient with admin user authentication."""
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():

        async def override_get_current_user():
            return user_schemas.UserRead.model_validate(admin_user)

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://test/api/v1"
        ) as client:
            yield client

        app.dependency_overrides = {}


@pytest.fixture
async def hr_client(hr_user: User):
    """Provide an AsyncClient with hr_user authentication."""
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():

        async def override_get_current_user():
            return user_schemas.UserRead.model_validate(hr_user)

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://test/api/v1"
        ) as client:
            yield client

        app.dependency_overrides = {}


@pytest.fixture
async def employee_client(employee_user: User):
    """Provide an AsyncClient with regular employee user authentication."""
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():

        async def override_get_current_user():
            return user_schemas.UserRead.model_validate(employee_user)

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://test/api/v1"
        ) as client:
            yield client

        app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def auth_client():
    """Provide an AsyncClient without any authentication."""
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():
        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://test/api/v1"
        ) as client:
            yield client


async def get_employee_client(user_id: int):
    sessions_service = SessionsService()
    session_id = await sessions_service.create_session(
        user_id, settings.SESSION_EXPIRE_TIME
    )
    csrf_token = await sessions_service.get_csrf_token(session_id)
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():
        client = AsyncClient(
            transport=ASGITransport(app),
            base_url="http://test/api/v1",
            cookies={
                settings.SESSION_COOKIE_NAME: session_id,
                settings.CSRF_COOKIE_NAME: csrf_token,
            },
        )
        return client


# ElasticSearch fixtures


@pytest.fixture(scope="function")
async def search_service() -> SearchService:
    service = SearchService()
    yield service
    await service.close()


@pytest.fixture(scope="function")
async def setup_indices(search_service) -> None:
    await search_service.create_benefits_index()
    await search_service.create_users_index()
    yield
    await search_service.es.options(ignore_status=[400, 404]).indices.delete(
        index=search_service.users_index_name
    )
    await search_service.es.options(ignore_status=[400, 404]).indices.delete(
        index=search_service.benefits_index_name
    )


@pytest.fixture(autouse=True)
async def mock_elasticsearch(request) -> None:
    if "elastic" not in request.keywords:
        app.dependency_overrides[SearchService.get_es_client] = lambda: None

        yield

        app.dependency_overrides = {}

    else:
        yield
