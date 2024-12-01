from datetime import date, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

import src.schemas.user as schemas
from src.models import User
from src.services.sessions import SessionsService
from src.services.users import UsersService
from tests.conftest import get_employee_client


@pytest.mark.parametrize(
    "field_name, field_value, expected_status",
    [
        ("firstname", "", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("firstname", "A" * 101, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("lastname", "", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("lastname", "B" * 101, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("email", "invalid-email", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("email", "user-valid123@example.com", status.HTTP_201_CREATED),
    ],
)
@pytest.mark.asyncio
async def test_create_user_required_fields(
    hr_client: AsyncClient, field_name: str, field_value: str, expected_status: int
):
    user_data = {
        "email": "testuser@example.com",
        "firstname": "Test",
        "lastname": "User",
        "role": "employee",
        "hired_at": date.today().isoformat(),
        "legal_entity_id": 111,
    }
    user_data[field_name] = field_value

    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "hired_at, expected_status",
    [
        (
            (date.today() + timedelta(days=1)).isoformat(),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),  # Future date
        (
            (date.today() - timedelta(days=365 * 5)).isoformat(),
            status.HTTP_201_CREATED,
        ),  # Past date
    ],
)
@pytest.mark.asyncio
async def test_create_user_hired_at(
    hr_client: AsyncClient, hired_at: str, expected_status: int
):
    user_data = {
        "email": "testuser@example.com",
        "firstname": "Test",
        "lastname": "User",
        "role": "employee",
        "hired_at": hired_at,
        "legal_entity_id": 111,
    }
    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_hr_cannot_update_user_outside_legal_entity(
    hr_client: AsyncClient, legal_entity2b, admin_user: User
):
    # Create a user in a different legal_entity
    user_data = {
        "email": "otherentityuser@example.com",
        "firstname": "Other",
        "lastname": "EntityUser",
        "role": "employee",
        "legal_entity_id": 222,
        "hired_at": date.today().isoformat(),
    }
    admin_user_data = schemas.UserRead.model_validate(admin_user)

    valid_user_data = schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()

    assert created_user_data["id"] is not None

    update_data = {
        "firstname": "UpdatedName",
    }
    update_response = await hr_client.patch(
        f"/users/{created_user_data['id']}", json=update_data
    )
    assert update_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_hr_can_update_user_in_legal_entity(hr_client: AsyncClient):
    # HR creates a user in their legal_entity
    user_data = {
        "email": "sameentityuser@example.com",
        "firstname": "Same",
        "lastname": "EntityUser",
        "role": "employee",
        "legal_entity_id": 111,
        "hired_at": date.today().isoformat(),
    }
    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    user = response.json()

    update_data = {
        "firstname": "Updated",
    }
    update_response = await hr_client.patch(f"/users/{user['id']}", json=update_data)
    assert update_response.status_code == status.HTTP_200_OK
    updated_user = update_response.json()
    assert updated_user["firstname"] == "Updated"

    update_data = {
        "role": "admin",
    }

    update_response = await hr_client.patch(f"/users/{user['id']}", json=update_data)
    assert update_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "field, value, expected_status",
    [
        ("role", "admin", status.HTTP_403_FORBIDDEN),
        (
            "hired_at",
            "2010-01-01",
            status.HTTP_403_FORBIDDEN,
        ),
        ("legal_entity_id", 111, status.HTTP_403_FORBIDDEN),
        ("is_adapted", True, status.HTTP_403_FORBIDDEN),
        ("firstname", "Sigma", status.HTTP_200_OK),
    ],
)
@pytest.mark.asyncio
async def test_employee_update(admin_user: User, field, value, expected_status):
    user_data = {
        "email": "updatinguser@example.com",
        "firstname": "Updating",
        "lastname": "User",
        "role": "employee",
        "hired_at": date.today().isoformat(),
    }
    admin_user_data = schemas.UserRead.model_validate(admin_user)

    valid_user_data = schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    user_id = created_user_data["id"]

    assert user_id is not None

    update_data = {
        field: value,
    }

    employee_client = await get_employee_client(user_id)

    update_response = await employee_client.patch(f"/users/{user_id}", json=update_data)
    assert update_response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        user = await UsersService().read_by_id(user_id)

        assert value == getattr(user, field)


@pytest.mark.asyncio
async def test_hr_cannot_create_admin(hr_client: AsyncClient):
    user_data = {
        "email": "adminuser321@example.com",
        "firstname": "Admin",
        "lastname": "User",
        "role": "admin",
        "legal_entity_id": 111,
        "hired_at": date.today().isoformat(),
    }
    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_employee_cannot_create_user(employee_client: AsyncClient):
    user_data = {
        "email": "unauthorizeduser@example.com",
        "firstname": "Unauthorized",
        "lastname": "User",
        "role": "employee",
        "legal_entity_id": 111,
        "hired_at": date.today().isoformat(),
    }
    response = await employee_client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_user_with_position(hr_client: AsyncClient):
    position_data = {
        "name": "Data Analyst",
    }
    position_response = await hr_client.post("/positions/", json=position_data)
    assert position_response.status_code == status.HTTP_201_CREATED
    position = position_response.json()

    user_data = {
        "email": "positionuser@example.com",
        "firstname": "Position",
        "lastname": "User",
        "role": "employee",
        "position_id": position["id"],
        "legal_entity_id": 111,
        "hired_at": date.today().isoformat(),
    }
    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    user = response.json()
    assert user["position"]["id"] == position["id"]
    assert user["position"]["name"] == position["name"]


# Testing AUTH endpoints


@pytest.mark.asyncio
async def test_user_auth(auth_client: AsyncClient, admin_user: User):
    user_data = {
        "email": "newuser@example.com",
        "firstname": "New",
        "lastname": "User",
        "role": "employee",
        "hired_at": date.today().isoformat(),
        "is_verified": False,
    }

    admin_user_data = schemas.UserRead.model_validate(admin_user)

    valid_user_data = schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    user_id = created_user_data["id"]

    verify_data = {"email": "newuser@example.com"}
    verify_response = await auth_client.post("/auth/verify", json=verify_data)
    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.json()["id"] == user_id

    register_data = {
        "id": user_id,
        "password": "securepassword",
        "re_password": "securepassword",
    }

    user = await UsersService().read_by_id(user_id)
    assert user.is_verified is False

    register_response = await auth_client.post("/auth/signup", json=register_data)
    assert register_response.status_code == status.HTTP_200_OK
    assert register_response.json()["is_success"] is True

    user = await UsersService().read_by_id(user_id)
    assert user.is_verified is True

    login_data = {
        "email": "newuser@example.com",
        "password": "securepassword",
    }

    user = await UsersService().read_by_email(login_data["email"])
    assert user is not None

    signin_response = await auth_client.post("/auth/signin", json=login_data)
    assert signin_response.status_code == status.HTTP_200_OK
    assert signin_response.json()["is_success"] is True

    cookies = signin_response.cookies
    assert cookies is not None

    session = await SessionsService().get_session(cookies["session_id"])

    assert session is not None
    assert session.session_id == cookies["session_id"]

    logout_response = await auth_client.post(
        "/auth/logout", cookies={"session_id": cookies["session_id"]}
    )
    assert logout_response.status_code == status.HTTP_200_OK, "Logout failed"
    assert logout_response.json()["is_success"] is True


@pytest.mark.asyncio
async def test_user_signin_invalid(auth_client: AsyncClient, admin_user: User):
    user_data = {
        "email": "newuser2@example.com",
        "firstname": "New",
        "lastname": "User",
        "role": "employee",
        "hired_at": date.today().isoformat(),
        "is_verified": False,
    }

    admin_user_data = schemas.UserRead.model_validate(admin_user)

    valid_user_data = schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    user_id = created_user_data["id"]

    register_data = {
        "id": user_id,
        "password": "securepassword",
        "re_password": "securepassword",
    }

    register_response = await auth_client.post("/auth/signup", json=register_data)
    assert register_response.status_code == status.HTTP_200_OK
    assert register_response.json()["is_success"] is True

    login_data = {
        "email": "newuser2@example.com",
        "password": "wrongpassword123",
    }

    user = await UsersService().read_by_email(login_data["email"])
    assert user is not None

    signin_response = await auth_client.post("/auth/signin", json=login_data)
    assert signin_response.status_code == status.HTTP_400_BAD_REQUEST


# Testing ELASTIC endpoints


@pytest.mark.parametrize("num_users", [1, 2, 4])
@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_user_creation(
    hr_client: AsyncClient,
    num_users,
    legal_entity1a,
    setup_indices,
):
    for i in range(num_users):
        user_data = {
            "email": f"elasticuser{i}@example.com",
            "firstname": "Elastic",
            "lastname": "Search",
            "role": "employee",
            "hired_at": date.today().isoformat(),
            "legal_entity_id": legal_entity1a.id,
        }
        response = await hr_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        user_in_db = await UsersService().read_by_id(response.json()["id"])
        assert user_in_db is not None

    get_response = await hr_client.get("/users/")
    assert len(get_response.json()) == num_users


@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_user_filter_by_role(
    hr_client: AsyncClient,
    setup_indices,
):
    users_data = [
        {
            "email": "employee1elastic@example.com",
            "firstname": "Employee",
            "lastname": "One",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
        {
            "email": "hr1elastic@example.com",
            "firstname": "HR",
            "lastname": "One",
            "role": "hr",
            "hired_at": date.today().isoformat(),
        },
        {
            "email": "employee2elastic@example.com",
            "firstname": "Employee",
            "lastname": "Two",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
    ]

    for user_data in users_data:
        response = await hr_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

    params = {"roles": ["employee", "hr"]}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 3

    params = {"roles": ["hr"]}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 1
    assert users[0]["role"] == "hr"


@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_user_sort_by_hired_at(
    hr_client: AsyncClient,
    setup_indices,
):
    users_data = [
        {
            "email": "user1@example.com",
            "firstname": "User",
            "lastname": "One",
            "role": "employee",
            "hired_at": (date.today() - timedelta(days=10)).isoformat(),
        },
        {
            "email": "user2@example.com",
            "firstname": "User",
            "lastname": "Two",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
        {
            "email": "user3@example.com",
            "firstname": "User",
            "lastname": "Three",
            "role": "employee",
            "hired_at": (date.today() - timedelta(days=5)).isoformat(),
        },
    ]

    for user_data in users_data:
        response = await hr_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

    params = {"sort_by": "hired_at", "sort_order": "asc"}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    hired_dates = [user["hired_at"] for user in users]
    assert hired_dates == sorted(hired_dates)

    params = {"sort_by": "hired_at", "sort_order": "desc"}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    hired_dates = [user["hired_at"] for user in users]
    assert hired_dates == sorted(hired_dates, reverse=True)


@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_user_search(
    hr_client: AsyncClient,
    setup_indices,
):
    users_data = [
        {
            "email": "alice@example.com",
            "firstname": "Alice",
            "lastname": "User",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
        {
            "email": "bob@example.com",
            "firstname": "Bob",
            "lastname": "User",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
        {
            "email": "charlie@example.com",
            "firstname": "Charlie",
            "lastname": "User",
            "role": "employee",
            "hired_at": date.today().isoformat(),
        },
    ]

    for user_data in users_data:
        response = await hr_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

    params = {"query": "Alice User"}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 3
    assert users[0]["firstname"] == "Alice"

    params = {"query": "cha"}
    response = await hr_client.get("/users/", params=params)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) == 1
    assert users[0]["firstname"] == "Charlie"
