from datetime import date

import pytest
from fastapi import status
from httpx import AsyncClient

import src.schemas.benefit as benefit_schemas
import src.schemas.user as user_schemas
from src.models import User
from src.schemas.request import BenefitStatus
from src.services.benefits import BenefitsService
from src.services.users import UsersService
from tests.conftest import get_employee_client


@pytest.mark.parametrize(
    "invalid_data, expected_status",
    [
        # Missing benefit_id
        (
            {
                "user_id": 444,
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
                "user_id": 444,
                "status": "invalid_status",
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid data type for status
        (
            {
                "benefit_id": 1,
                "user_id": 444,
                "status": 123,
                "comment": "Test comment",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_pairwise(
    benefit_data, user_data, admin_client: AsyncClient, hr_client: AsyncClient
):
    # Create benefit
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit = benefit_response.json()
    benefit_id = benefit["id"]

    # Create user
    user_response = await hr_client.post("/users/", json=user_data)
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
    assert benefit_request["user"]["id"] == user_id
    assert benefit_request["benefit"]["id"] == benefit_id


async def perform_benefit_request_test(
    admin_user: User,
    benefit_data: dict,
    user_data: dict,
    expected_status: int,
):
    # Create Benefit
    valid_benefit_data = benefit_schemas.BenefitCreate.model_validate(benefit_data)

    created_benefit = await BenefitsService().create(valid_benefit_data)

    created_benefit_data = created_benefit.model_dump()
    assert created_benefit_data["id"] is not None

    # Create User
    admin_user_data = user_schemas.UserRead.model_validate(admin_user)

    valid_user_data = user_schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
        "user_id": created_user_data["id"],
    }
    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == expected_status


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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
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
                "legal_entity_id": 111,
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

    valid_benefit_data = benefit_schemas.BenefitCreate.model_validate(benefit_data)

    created_benefit = await BenefitsService().create(valid_benefit_data)

    created_benefit_data = created_benefit.model_dump()
    assert created_benefit_data["id"] is not None

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

    admin_user_data = user_schemas.UserRead.model_validate(admin_user)
    valid_user_data = user_schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
        "user_id": created_user_data["id"],
    }

    request_create_response = await employee_client.post(
        "/benefit-requests/", json=request_data
    )
    assert request_create_response.status_code == status.HTTP_201_CREATED

    benefit_request = request_create_response.json()

    request_id = benefit_request["id"]

    benefit_response = await BenefitsService().read_by_id(created_benefit_data["id"])
    updated_benefit_data = benefit_response.model_dump()
    assert updated_benefit_data["amount"] == benefit_data["amount"] - 1

    user_response = await UsersService().read_by_id(created_user_data["id"])
    updated_user_data = user_response.model_dump()
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
