from datetime import date, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.users import UsersService


async def create_user_test(client: AsyncClient, user_data: dict, expected_status: int):
    response = await client.post("/users/", json=user_data)

    assert response.status_code == expected_status

    if response.status_code == status.HTTP_201_CREATED:
        data = response.json()

        user_service_data = await UsersService().read_by_id(data["id"])

        assert user_service_data is not None

        user_data = (user_service_data).model_dump()

        del user_data["hired_at"]
        del data["hired_at"]

        assert user_data == data


user_data_cases_for_hr = [
    # Test 1: HR creates EMPLOYEE in own legal_entity_id=111
    (
        {
            "email": "employee1@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "role": "employee",
            "coins": 0,
            "legal_entity_id": 111,
            "hired_at": date.today().isoformat(),
            "is_active": True,
        },
        status.HTTP_201_CREATED,
    ),
    # Test 2: HR creates HR in own legal_entity_id=111
    (
        {
            "email": "hr_new@example.com",
            "firstname": "Alice",
            "lastname": "Smith",
            "role": "hr",
            "coins": 100,
            "legal_entity_id": 111,
            "hired_at": (date.today() - timedelta(days=365)).isoformat(),
            "is_active": False,
        },
        status.HTTP_201_CREATED,
    ),
]
user_data_cases_for_admin = [
    # Test 3: Admin creates EMPLOYEE in legal_entity_id=222
    (
        {
            "email": "employee2@example.com",
            "firstname": "Jane",
            "lastname": "Doe",
            "role": "employee",
            "coins": 100,
            "legal_entity_id": 222,
            "hired_at": (date.today() - timedelta(days=365)).isoformat(),
            "is_active": False,
        },
        status.HTTP_201_CREATED,
    ),
    # Test 4: Admin creates HR in legal_entity_id=222
    (
        {
            "email": "hr_other@example.com",
            "firstname": "Bob",
            "lastname": "Johnson",
            "role": "hr",
            "coins": 0,
            "legal_entity_id": 222,
            "hired_at": date.today().isoformat(),
            "is_active": True,
        },
        status.HTTP_201_CREATED,
    ),
    # Test 5: Admin creates ADMIN in legal_entity_id=111
    (
        {
            "email": "admin123@example.com",
            "firstname": "Admin",
            "lastname": "One",
            "role": "admin",
            "coins": 0,
            "legal_entity_id": 111,
            "hired_at": date.today().isoformat(),
            "is_active": True,
        },
        status.HTTP_201_CREATED,
    ),
    # Test 6: Admin creates ADMIN in legal_entity_id=222
    (
        {
            "email": "admin124@example.com",
            "firstname": "Admin",
            "lastname": "Two",
            "role": "admin",
            "coins": 100,
            "legal_entity_id": 222,
            "hired_at": (date.today() - timedelta(days=365)).isoformat(),
            "is_active": False,
        },
        status.HTTP_201_CREATED,
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("user_data, expected_status", user_data_cases_for_hr)
async def test_create_user_hr_client(
    hr_client: AsyncClient, user_data: dict, expected_status: int
):
    await create_user_test(hr_client, user_data, expected_status)


@pytest.mark.asyncio
@pytest.mark.parametrize("user_data, expected_status", user_data_cases_for_admin)
async def test_create_user_admin_client(
    admin_client: AsyncClient,
    user_data: dict,
    expected_status: int,
    legal_entity1a,
    legal_entity2b,
):
    await create_user_test(admin_client, user_data, expected_status)


@pytest.mark.parametrize(
    "user_data, expected_status",
    [
        # Missing required fields
        (
            {
                # Missing 'email'
                "firstname": "NoEmail",
                "lastname": "User",
                "role": "employee",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            {
                "email": "invaliduser@example.com",
                # Missing 'firstname'
                "lastname": "User",
                "role": "employee",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid email format
        (
            {
                "email": "invalid-email",
                "firstname": "InvalidEmail",
                "lastname": "User",
                "role": "employee",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid role
        (
            {
                "email": "unknownrole@example.com",
                "firstname": "Unknown",
                "lastname": "Role",
                "role": "unknown",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Negative coins
        (
            {
                "email": "negativecoins@example.com",
                "firstname": "Negative",
                "lastname": "Coins",
                "role": "employee",
                "coins": -10,
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Future 'hired_at' date
        (
            {
                "email": "futuredate@example.com",
                "firstname": "Future",
                "lastname": "Date",
                "role": "employee",
                "hired_at": (date.today() + timedelta(days=1)).isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Long firstname
        (
            {
                "email": "longfirstname@example.com",
                "firstname": "A" * 101,
                "lastname": "User",
                "role": "employee",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # HR tries to create admin (should be forbidden)
        (
            {
                "email": "hrcreatesadmin@example.com",
                "firstname": "HR",
                "lastname": "Admin",
                "role": "admin",
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_403_FORBIDDEN,
        ),
        # HR tries to create user in different legal entity
        (
            {
                "email": "otherentityuser@example.com",
                "firstname": "Other",
                "lastname": "Entity",
                "role": "employee",
                "legal_entity_id": 222,
                "hired_at": date.today().isoformat(),
            },
            status.HTTP_403_FORBIDDEN,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_users_invalid(
    hr_client: AsyncClient, user_data: dict, expected_status: int
):
    response = await hr_client.post("/users/", json=user_data)
    assert response.status_code == expected_status
