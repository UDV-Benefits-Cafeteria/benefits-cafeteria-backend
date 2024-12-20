from decimal import Decimal

import pytest
from fastapi import status
from httpx import AsyncClient

from src.models import User
from src.schemas.benefit import BenefitReadPublic
from src.schemas.user import UserRead
from src.services.benefits import BenefitsService


@pytest.mark.parametrize(
    "benefit_data",
    [
        # Test 1
        {
            "name": "Benefit Test 1",
            "coins_cost": 0,
            "min_level_cost": 0,
            "amount": None,
            "adaptation_required": True,
            "category_id": 111,
        },
        # Test 2
        {
            "name": "Benefit Test 2",
            "coins_cost": 0,
            "min_level_cost": 5,
            "amount": 0,
            "adaptation_required": False,
            "category_id": None,
            "real_currency_cost": 505.5,
        },
        # Test 3
        {
            "name": "Benefit Test 3",
            "coins_cost": 0,
            "min_level_cost": 10,
            "amount": 10,
            "adaptation_required": True,
            "category_id": 111,
        },
        # Test 4
        {
            "name": "Benefit Test 4",
            "coins_cost": 10,
            "min_level_cost": 0,
            "amount": 0,
            "adaptation_required": True,
            "category_id": None,
        },
        # Test 5
        {
            "name": "Benefit Test 5",
            "coins_cost": 10,
            "min_level_cost": 5,
            "amount": 10,
            "adaptation_required": False,
            "category_id": 111,
            "real_currency_cost": 2000,
        },
        # Test 6
        {
            "name": "Benefit Test 6",
            "coins_cost": 10,
            "min_level_cost": 10,
            "amount": None,
            "adaptation_required": False,
            "category_id": None,
        },
        # Test 7
        {
            "name": "Benefit Test 7",
            "coins_cost": 100,
            "min_level_cost": 0,
            "amount": 10,
            "adaptation_required": False,
            "category_id": 111,
        },
        # Test 8
        {
            "name": "Benefit Test 8",
            "coins_cost": 100,
            "min_level_cost": 5,
            "amount": None,
            "adaptation_required": True,
            "category_id": None,
        },
        # Test 9
        {
            "name": "Benefit Test 9",
            "coins_cost": 100,
            "min_level_cost": 10,
            "amount": 0,
            "adaptation_required": True,
            "category_id": 111,
        },
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_valid(
    admin_client: AsyncClient,
    benefit_data: dict,
    employee_user: User,
    category,
):
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    benefit_id_db: BenefitReadPublic = await BenefitsService().read_by_id(
        data["id"], UserRead.model_validate(employee_user)
    )
    assert benefit_id_db is not None

    assert benefit_id_db.model_dump().get("real_currency_cost") is None

    for key in benefit_data:
        if key == "category_id":
            if benefit_data["category_id"] is not None:
                assert data["category"]["id"] == benefit_data["category_id"]
                assert data["category"]["id"] == getattr(benefit_id_db, "category").id
            else:
                assert data["category"] is None
                assert getattr(benefit_id_db, "category") is None
        elif key == "real_currency_cost":
            assert Decimal(data[key]) == benefit_data[key]
        else:
            assert data[key] == benefit_data[key]
            assert data[key] == getattr(benefit_id_db, key)


@pytest.mark.parametrize(
    "benefit_data",
    [
        # Missing required fields
        {
            # Missing 'name'
            "coins_cost": 10,
            "min_level_cost": 0,
        },
        {
            "name": "Missing Coins Cost",
            "min_level_cost": 0,
        },
        {
            "name": "Missing Min Level Cost",
            "coins_cost": 10,
        },
        # Invalid data types
        {
            "name": "Invalid Coins Cost Type",
            "coins_cost": "ten",
            "min_level_cost": 0,
        },
        {
            "name": "Invalid Min Level Cost Type",
            "coins_cost": 10,
            "min_level_cost": "zero",
        },
        # Negative values
        {
            "name": "Negative Coins Cost",
            "coins_cost": -10,
            "min_level_cost": 0,
        },
        {
            "name": "Negative Min Level Cost",
            "coins_cost": 10,
            "min_level_cost": -5,
        },
        # Invalid name length
        {
            "name": "A" * 101,
            "coins_cost": 10,
            "min_level_cost": 0,
        },
        # Invalid category_id
        {
            "name": "Invalid Category ID",
            "coins_cost": 10,
            "min_level_cost": 0,
            "category_id": "one",
        },
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_invalid(admin_client: AsyncClient, benefit_data):
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
