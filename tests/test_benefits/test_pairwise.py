import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.parametrize(
    "benefit_data, expected_status",
    [
        # Test 1
        (
            {
                "name": "Benefit Test 1",
                "coins_cost": 0,
                "min_level_cost": 0,
                "amount": None,
                "adaptation_required": True,
                "category_id": 1,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 2
        (
            {
                "name": "Benefit Test 2",
                "coins_cost": 0,
                "min_level_cost": 5,
                "amount": 0,
                "adaptation_required": False,
                "category_id": None,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 3
        (
            {
                "name": "Benefit Test 3",
                "coins_cost": 0,
                "min_level_cost": 10,
                "amount": 10,
                "adaptation_required": True,
                "category_id": 1,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 4
        (
            {
                "name": "Benefit Test 4",
                "coins_cost": 10,
                "min_level_cost": 0,
                "amount": 0,
                "adaptation_required": True,
                "category_id": None,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 5
        (
            {
                "name": "Benefit Test 5",
                "coins_cost": 10,
                "min_level_cost": 5,
                "amount": 10,
                "adaptation_required": False,
                "category_id": 1,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 6
        (
            {
                "name": "Benefit Test 6",
                "coins_cost": 10,
                "min_level_cost": 10,
                "amount": None,
                "adaptation_required": False,
                "category_id": None,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 7
        (
            {
                "name": "Benefit Test 7",
                "coins_cost": 100,
                "min_level_cost": 0,
                "amount": 10,
                "adaptation_required": False,
                "category_id": 1,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 8
        (
            {
                "name": "Benefit Test 8",
                "coins_cost": 100,
                "min_level_cost": 5,
                "amount": None,
                "adaptation_required": True,
                "category_id": None,
            },
            status.HTTP_201_CREATED,
        ),
        # Test 9
        (
            {
                "name": "Benefit Test 9",
                "coins_cost": 100,
                "min_level_cost": 10,
                "amount": 0,
                "adaptation_required": True,
                "category_id": 1,
            },
            status.HTTP_201_CREATED,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_pairwise(
    admin_client: AsyncClient, benefit_data: dict, expected_status: int
):
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status

    if response.status_code == status.HTTP_201_CREATED:
        data = response.json()
        for key in benefit_data:
            if key != "category_id":
                assert data[key] == benefit_data[key]
            else:
                assert data["category"]["id"] == benefit_data["category_id"]


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
