from datetime import date

import pytest
from fastapi import status
from httpx import AsyncClient

import src.schemas.benefit as benefit_schemas
import src.schemas.user as user_schemas
from src.models import User
from src.services.benefits import BenefitsService
from src.services.users import UsersService
from tests.conftest import get_employee_client


async def create_test_benefit(benefit_data: dict) -> dict:
    valid_benefit_data = benefit_schemas.BenefitCreate.model_validate(benefit_data)

    created_benefit = await BenefitsService().create(valid_benefit_data)

    created_benefit_data = created_benefit.model_dump()
    assert created_benefit_data["id"] is not None

    return created_benefit_data


async def create_test_user(user_data: dict, executing_user: User) -> dict:
    admin_user_data = user_schemas.UserRead.model_validate(executing_user)

    valid_user_data = user_schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    return created_user_data


async def perform_benefit_request_test(
    admin_user: User,
    benefit_data: dict,
    user_data: dict,
    expected_status: int,
) -> dict:
    # Create Benefit
    created_benefit_data = await create_test_benefit(benefit_data)

    # Create User
    created_user_data = await create_test_user(user_data, admin_user)

    # Authenticate as created user
    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
    }

    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == expected_status

    return {
        "benefit_request": response.json(),
        "user": created_user_data,
        "benefit": created_benefit_data,
    }


@pytest.mark.parametrize(
    "invalid_data, expected_status",
    [
        # Missing benefit_id
        (
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid benefit_id type
        (
            {"benefit_id": "invalid_id"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Benefit does not exist
        (
            {"benefit_id": 9999},
            status.HTTP_404_NOT_FOUND,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_invalid_data(
    invalid_data, expected_status, employee_client: AsyncClient
):
    response = await employee_client.post("/benefit-requests/", json=invalid_data)
    assert response.status_code == expected_status


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
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_pairwise(
    benefit_data: dict, user_data: dict, admin_user: User
):
    test_data = await perform_benefit_request_test(
        admin_user, benefit_data, user_data, status.HTTP_201_CREATED
    )

    benefit_request = test_data["benefit_request"]
    user = test_data["user"]
    benefit = test_data["benefit"]

    assert benefit_request["status"] == "pending"
    assert benefit_request["user"]["id"] == user["id"]
    assert benefit_request["benefit"]["id"] == benefit["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "benefit_data, user_data, expected_status",
    [
        # Test 1: User does not have enough coins
        (
            {
                "name": "Benefit High Cost",
                "coins_cost": 20,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "user_insufficient_coins@example.com",
                "firstname": "Insufficient",
                "lastname": "Coins",
                "role": "employee",
                "coins": 10,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 2: User does not have minimal required level
        (
            {
                "name": "Benefit High Level",
                "coins_cost": 10,
                "min_level_cost": 12,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "user_low_level@example.com",
                "firstname": "Low",
                "lastname": "Level",
                "role": "employee",
                "coins": 20,
                "hired_at": date.today(),
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 3: User is not adapted and the benefit is requiring adaptation
        (
            {
                "name": "Benefit Requires Adaptation",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": True,
            },
            {
                "email": "user_not_adapted@example.com",
                "firstname": "NotAdapted",
                "lastname": "User",
                "role": "employee",
                "coins": 20,
                "hired_at": "2022-01-01",
                "is_adapted": False,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 4: Not enough amount of benefits
        (
            {
                "name": "Benefit Out of Stock",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 0,
                "adaptation_required": False,
            },
            {
                "email": "user_benefit_amount_insufficient@example.com",
                "firstname": "Benefit",
                "lastname": "AmountInsufficient",
                "role": "employee",
                "coins": 20,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
async def test_benefit_request_invalid_conditions(
    admin_user: User,
    benefit_data: dict,
    user_data: dict,
    expected_status: int,
):
    await perform_benefit_request_test(
        admin_user=admin_user,
        benefit_data=benefit_data,
        user_data=user_data,
        expected_status=expected_status,
    )


@pytest.mark.asyncio
async def test_cancel_benefit_request_restores_coins_and_amount(
    admin_user: User, legal_entity1a
):
    benefit_data = {
        "name": "Benefit Cancel Test",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }

    user_data = {
        "email": "user_cancel_test@example.com",
        "firstname": "Cancel",
        "lastname": "Test",
        "role": "employee",
        "coins": 20,
        "hired_at": "2022-01-01",
        "is_adapted": True,
        "legal_entity_id": 111,
    }

    created_benefit_data = await create_test_benefit(benefit_data)

    created_user_data = await create_test_user(user_data, admin_user)

    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
    }

    request_create_response = await employee_client.post(
        "/benefit-requests/", json=request_data
    )
    assert request_create_response.status_code == status.HTTP_201_CREATED

    benefit_request = request_create_response.json()

    request_id = benefit_request["id"]

    benefit_response = await BenefitsService().read_by_id(created_benefit_data["id"])
    updated_benefit_data = benefit_response.model_dump()
    user_response = await UsersService().read_by_id(created_user_data["id"])
    updated_user_data = user_response.model_dump()

    assert updated_benefit_data["amount"] == benefit_data["amount"] - 1
    assert updated_user_data["coins"] == user_data["coins"] - benefit_data["coins_cost"]

    update_data = {
        "status": "declined",
    }

    response = await employee_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )

    assert response.status_code == status.HTTP_200_OK

    updated_request = response.json()
    assert updated_request["status"] == "declined"

    restored_benefit_response = await BenefitsService().read_by_id(
        created_benefit_data["id"]
    )

    restored_benefit_data = restored_benefit_response.model_dump()
    assert restored_benefit_data["amount"] == benefit_data["amount"]

    restored_user_response = await UsersService().read_by_id(created_user_data["id"])
    restored_user_data = restored_user_response.model_dump()

    assert restored_user_data["coins"] == user_data["coins"]


@pytest.mark.asyncio
async def test_benefit_request_transaction(admin_user: User, legal_entity1a):
    benefit_data = {
        "name": "Benefit Transaction Test",
        "coins_cost": 50,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }

    user_data = {
        "email": "user_transaction_test@example.com",
        "firstname": "Transaction",
        "lastname": "Test",
        "role": "employee",
        "coins": 10,  # Not Enough
        "hired_at": "2022-01-01",
        "is_adapted": True,
        "legal_entity_id": 111,
    }
    created_benefit_data = await create_test_benefit(benefit_data)

    created_user_data = await create_test_user(user_data, admin_user)

    benefit_id = created_benefit_data["id"]
    user_id = created_user_data["id"]

    assert user_id is not None

    employee_client = await get_employee_client(user_id)

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }

    request_create_response = await employee_client.post(
        "/benefit-requests/", json=request_data
    )

    assert request_create_response.status_code == status.HTTP_400_BAD_REQUEST

    benefit_after_operation = await BenefitsService().read_by_id(benefit_id)
    # Check that amount didn't change meaning transaction had a rollback
    assert benefit_after_operation.amount == 5

    user_after_operation = await UsersService().read_by_id(user_id)
    assert user_after_operation.coins == 10
