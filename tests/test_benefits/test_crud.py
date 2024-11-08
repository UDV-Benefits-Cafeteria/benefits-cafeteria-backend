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
async def test_get_benefit_valid(admin_client: AsyncClient):
    response = await admin_client.get("/benefits/1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_benefit_invalid(admin_client: AsyncClient):
    response = await admin_client.get("/benefits/9999")
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
    admin_client: AsyncClient, coins_cost, expected_status
):
    benefit_data = {
        "name": f"Benefit Coins Cost {coins_cost}",
        "coins_cost": coins_cost,
        "min_level_cost": 0,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
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
    admin_client: AsyncClient, amount, expected_status
):
    benefit_data = {
        "name": f"Benefit Amount {amount}",
        "coins_cost": 10,
        "min_level_cost": 0,
        "amount": amount,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
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
    admin_client: AsyncClient, name, expected_status
):
    benefit_data = {
        "name": name,
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_update_benefit(admin_client: AsyncClient, category):
    benefit_data = {
        "name": "Original Benefit",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    create_response = await admin_client.post("/benefits/", json=benefit_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    benefit = create_response.json()

    update_data = {
        "name": "Updated Benefit",
        "coins_cost": 20,
        "category_id": category.id,
    }
    update_response = await admin_client.patch(
        f"/benefits/{benefit['id']}", json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_benefit = update_response.json()
    assert updated_benefit["name"] == update_data["name"]
    assert updated_benefit["coins_cost"] == update_data["coins_cost"]
    assert updated_benefit["category_id"] == update_data["category_id"]


@pytest.mark.asyncio
async def test_update_benefit_invalid(admin_client: AsyncClient):
    update_data = {
        "name": "Updated Benefit",
        "coins_cost": 20,
    }
    response = await admin_client.patch("/benefits/9999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit(admin_client: AsyncClient):
    benefit_data = {
        "name": "Benefit to Delete",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    create_response = await admin_client.post("/benefits/", json=benefit_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    benefit = create_response.json()

    delete_response = await admin_client.delete(f"/benefits/{benefit['id']}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await admin_client.get(f"/benefits/{benefit['id']}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit_invalid(admin_client: AsyncClient):
    response = await admin_client.delete("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_with_extra_fields(admin_client: AsyncClient):
    benefit_data = {
        "name": "Benefit with Extra Fields",
        "coins_cost": 10,
        "min_level_cost": 0,
        "unknown_field": "some value",
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
    benefit = response.json()
    assert benefit.get("unknown_field") is None
