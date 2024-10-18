import pytest
from fastapi import status
from httpx import AsyncClient

benefit_data = {
    "name": "Health Insurance",
    "description": "Comprehensive health insurance for employees",
    "coins_cost": 5,
    "min_level_cost": 1,
}

benefit_update_data = {
    "name": "Updated Health Insurance",
    "description": "Updated description",
}

invalid_benefit_data = {
    "name": "",
    "description": "Invalid benefit",
}


@pytest.mark.asyncio
async def test_create_benefit_valid(async_client: AsyncClient):
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == benefit_data["name"]
    assert data["description"] == benefit_data["description"]


@pytest.mark.asyncio
async def test_create_benefit_invalid(async_client: AsyncClient):
    response = await async_client.post("/benefits/", json=invalid_benefit_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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


@pytest.mark.asyncio
async def test_update_benefit_valid(async_client: AsyncClient):
    response = await async_client.patch("/benefits/1", json=benefit_update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == benefit_update_data["name"]
    assert data["description"] == benefit_update_data["description"]


@pytest.mark.asyncio
async def test_update_benefit_invalid(async_client: AsyncClient):
    response = await async_client.patch("/benefits/9999", json=benefit_update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit_valid(async_client: AsyncClient):
    response = await async_client.delete("/benefits/1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_delete_benefit_invalid(async_client: AsyncClient):
    response = await async_client.delete("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
