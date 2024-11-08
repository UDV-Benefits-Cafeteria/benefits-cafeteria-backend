import pytest
from fastapi import status
from httpx import AsyncClient

from src.schemas.request import BenefitStatus
from tests.conftest import get_employee_client


@pytest.mark.parametrize(
    "invalid_data, expected_status",
    [
        # Missing benefit_id
        (
            {
                "user_id": 1,
                "status": BenefitStatus.PENDING,
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Missing user_id
        (
            {
                "benefit_id": 1,
                "status": BenefitStatus.PENDING,
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid status value
        (
            {
                "benefit_id": 1,
                "user_id": 1,
                "status": "invalid_status",
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid data type for status
        (
            {
                "benefit_id": 1,
                "user_id": 1,
                "status": 123,
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_invalid_data(
    invalid_data, expected_status, expected_detail, employee_client: AsyncClient
):
    response = await employee_client.post("/benefit-requests/", json=invalid_data)
    assert response.status_code == expected_status
    assert expected_detail.lower() in response.text.lower()


@pytest.mark.parametrize(
    "benefit_data, user_data",
    [
        # Test 1
        (
            {
                "name": "Benefit Adapted User",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": True,
            },
            {
                "email": "adapted_user@example.com",
                "firstname": "Adapted",
                "lastname": "User",
                "role": "employee",
                "coins": 20,
                "level": 1,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
        ),
        # Test 2
        (
            {
                "name": "Benefit High Level",
                "coins_cost": 15,
                "min_level_cost": 2,
                "amount": 5,
                "adaptation_required": True,
            },
            {
                "email": "high_level_user@example.com",
                "firstname": "High",
                "lastname": "Level",
                "role": "employee",
                "coins": 15,
                "level": 3,
                "hired_at": "2021-01-01",
                "is_adapted": True,
            },
        ),
        # Test 3
        (
            {
                "name": "Benefit Non-Adapted User",
                "coins_cost": 5,
                "min_level_cost": 2,
                "amount": 8,
                "adaptation_required": False,
            },
            {
                "email": "non_adapted_user@example.com",
                "firstname": "NonAdapted",
                "lastname": "User",
                "role": "employee",
                "coins": 10,
                "level": 3,
                "hired_at": "2020-01-01",
                "is_adapted": False,
            },
        ),
        # Test 4
        (
            {
                "name": "Benefit Adapted Enough Coins",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "adapted_enough_coins_user@example.com",
                "firstname": "AdaptedCoins",
                "lastname": "User",
                "role": "employee",
                "coins": 10,
                "level": 1,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_pairwise(
    benefit_data, user_data, admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit = benefit_response.json()
    benefit_id = benefit["id"]

    # Create user
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user = user_response.json()
    user_id = user["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED
    benefit_request = response.json()
    assert benefit_request["status"] == "pending"
    assert benefit_request["user_id"] == user_id
    assert benefit_request["benefit_id"] == benefit_id


@pytest.mark.asyncio
async def test_benefit_request_insufficient_coins(
    admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit
    benefit_data = {
        "name": "Benefit High Cost",
        "coins_cost": 20,
        "min_level_cost": 1,
        "amount": 10,
        "adaptation_required": False,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    # Create user with fewer coins than needed
    user_data = {
        "email": "user_insufficient_coins@example.com",
        "firstname": "Insufficient",
        "lastname": "Coins",
        "role": "employee",
        "coins": 10,
        "level": 1,
        "hired_at": "2022-01-01",
        "is_adapted": True,
    }
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Attempt to create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User does not have enough coins" in response.json()["detail"]


@pytest.mark.asyncio
async def test_benefit_request_level_requirement_not_met(
    admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit
    benefit_data = {
        "name": "Benefit High Level",
        "coins_cost": 10,
        "min_level_cost": 5,
        "amount": 10,
        "adaptation_required": False,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    # Create user with level less than required
    user_data = {
        "email": "user_low_level@example.com",
        "firstname": "Low",
        "lastname": "Level",
        "role": "employee",
        "coins": 20,
        "level": 2,
        "hired_at": "2022-01-01",
        "is_adapted": True,
    }
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Attempt to create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User does not have required level" in response.json()["detail"]


@pytest.mark.asyncio
async def test_benefit_request_adaptation_requirement_not_met(
    admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit requiring adapted users
    benefit_data = {
        "name": "Benefit Requires Adaptation",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 10,
        "adaptation_required": True,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    # Create user who is not adapted
    user_data = {
        "email": "user_not_adapted@example.com",
        "firstname": "NotAdapted",
        "lastname": "User",
        "role": "employee",
        "coins": 20,
        "level": 1,
        "hired_at": "2022-01-01",
        "is_adapted": False,
    }
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Attempt to create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User does not meet adaptation requirement" in response.json()["detail"]


@pytest.mark.asyncio
async def test_benefit_request_amount_insufficient(
    admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit with amount = 0
    benefit_data = {
        "name": "Benefit Out of Stock",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 0,
        "adaptation_required": False,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    # Create user
    user_data = {
        "email": "user_benefit_amount_insufficient@example.com",
        "firstname": "Benefit",
        "lastname": "AmountInsufficient",
        "role": "employee",
        "coins": 20,
        "level": 1,
        "hired_at": "2022-01-01",
        "is_adapted": True,
    }
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Attempt to create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Benefit amount is insufficient" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_benefit_request_restores_coins_and_amount(
    admin_client: AsyncClient, hr_client1: AsyncClient
):
    # Create benefit
    benefit_data = {
        "name": "Benefit Cancel Test",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit = benefit_response.json()
    benefit_id = benefit["id"]

    # Create user
    user_data = {
        "email": "user_cancel_test@example.com",
        "firstname": "Cancel",
        "lastname": "Test",
        "role": "employee",
        "coins": 20,
        "level": 1,
        "hired_at": "2022-01-01",
        "is_adapted": True,
    }
    user_response = await hr_client1.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user = user_response.json()
    user_id = user["id"]

    # Authenticate as the user
    employee_client = await get_employee_client(user_id)

    # Create benefit request
    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED
    benefit_request = response.json()
    request_id = benefit_request["id"]

    # Verify benefit amount decreased
    benefit_response = await admin_client.get(f"/benefits/{benefit_id}")
    updated_benefit = benefit_response.json()
    assert updated_benefit["amount"] == benefit_data["amount"] - 1

    # Verify user's coins decreased
    user_response = await hr_client1.get(f"/users/{user_id}")
    updated_user = user_response.json()
    assert updated_user["coins"] == user_data["coins"] - benefit_data["coins_cost"]

    # User cancels the benefit request (changes status to declined)
    update_data = {
        "status": "declined",
    }
    response = await employee_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    updated_request = response.json()
    assert updated_request["status"] == "declined"

    # Verify benefit amount restored
    benefit_response = await admin_client.get(f"/benefits/{benefit_id}")
    restored_benefit = benefit_response.json()
    assert restored_benefit["amount"] == benefit_data["amount"]

    # Verify user's coins restored
    user_response = await hr_client1.get(f"/users/{user_id}")
    restored_user = user_response.json()
    assert restored_user["coins"] == user_data["coins"]
