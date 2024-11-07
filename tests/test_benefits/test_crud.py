import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.parametrize(
    "benefit_data, expected_status",
    [
        # Valid cases
        (
            {
                "name": "Health Insurance",
                "description": "Comprehensive health insurance for employees",
                "coins_cost": 5,
                "min_level_cost": 1,
            },
            status.HTTP_201_CREATED,
        ),
        (
            {
                "name": "Dental Insurance",
                "description": "Dental insurance for employees",
                "coins_cost": 10,
                "min_level_cost": 3,
            },
            status.HTTP_201_CREATED,
        ),
        # Invalid cases
        (
            {
                "name": "",  # Invalid because name is empty
                "description": "Invalid benefit",
                "coins_cost": 5,
                "min_level_cost": 1,
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            {
                "name": "Health Insurance",
                "description": "Description exceeds allowed length"
                * 50,  # Exceeding max description length
                "coins_cost": 5,
                "min_level_cost": 1,
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            {
                "name": "Health Insurance",
                "description": "Valid description",
                "coins_cost": -1,  # Invalid because coins_cost is negative
                "min_level_cost": 1,
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            {
                "name": "Health Insurance",
                "description": "Valid description",
                "coins_cost": 5,
                "min_level_cost": -1,  # Invalid because min_level_cost is negative
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ],
)
@pytest.mark.asyncio
async def test_admin_create_benefit(
    async_admin_test_client: AsyncClient, benefit_data: dict, expected_status: str
):
    response = await async_admin_test_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status

    # Additional checks for valid cases
    if response.status_code == status.HTTP_201_CREATED:
        data = response.json()
        assert data["name"] == benefit_data["name"]
        assert data["description"] == benefit_data["description"]
        assert data["coins_cost"] == benefit_data["coins_cost"]
        assert data["min_level_cost"] == benefit_data["min_level_cost"]


@pytest.mark.asyncio
async def test_get_benefit_valid(async_client: AsyncClient):
    response = await async_client.get("/benefits/1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_benefit_invalid(async_client: AsyncClient):
    response = await async_client.get("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# @pytest.mark.asyncio
# async def test_update_benefit_valid(async_client: AsyncClient):
#     response = await async_client.patch("/benefits/1", json=benefit_update_data)
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["name"] == benefit_update_data["name"]
#     assert data["description"] == benefit_update_data["description"]
#
#
# @pytest.mark.asyncio
# async def test_update_benefit_invalid(async_client: AsyncClient):
#     response = await async_client.patch("/benefits/9999", json=benefit_update_data)
#     assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit_valid(async_client: AsyncClient):
    response = await async_client.delete("/benefits/1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_success"] is True


@pytest.mark.asyncio
async def test_delete_benefit_invalid(async_client: AsyncClient):
    response = await async_client.delete("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "coins_cost, expected_status",
    [
        (-1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (0, status.HTTP_201_CREATED),
        (1, status.HTTP_201_CREATED),
        (9999999, status.HTTP_201_CREATED),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_coins_cost_boundary(
    async_client: AsyncClient, coins_cost, expected_status
):
    benefit_data = {
        "name": f"Benefit Coins Cost {coins_cost}",
        "coins_cost": coins_cost,
        "min_level_cost": 0,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "amount, expected_status",
    [
        (-1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (0, status.HTTP_201_CREATED),
        (1, status.HTTP_201_CREATED),
        (None, status.HTTP_201_CREATED),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_amount_boundary(
    async_client: AsyncClient, amount, expected_status
):
    benefit_data = {
        "name": f"Benefit Amount {amount}",
        "coins_cost": 10,
        "min_level_cost": 0,
        "amount": amount,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "name, expected_status",
    [
        ("", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("A", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("AA", status.HTTP_201_CREATED),
        ("Valid Benefit Name", status.HTTP_201_CREATED),
        ("A" * 100, status.HTTP_201_CREATED),
        ("A" * 101, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_name_length(
    async_client: AsyncClient, name, expected_status
):
    benefit_data = {
        "name": name,
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status
