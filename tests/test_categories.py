import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_create_category_valid(async_client: AsyncClient):
    valid_category_data = {
        "name": "New Category",
    }
    response = await async_client.post("/categories/", json=valid_category_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_create_category_invalid(async_client: AsyncClient):
    invalid_category_data = {
        "name": "",
    }
    response = await async_client.post("/categories/", json=invalid_category_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_category_not_found(async_client: AsyncClient):
    category_id = 9999
    response = await async_client.get(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_categories(async_client: AsyncClient):
    response = await async_client.get("/categories/")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_category_not_found(async_client: AsyncClient):
    category_id = 9999
    update_data = {
        "name": "Updated Category",
    }
    response = await async_client.patch(f"/categories/{category_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_category_invalid(async_client: AsyncClient):
    category_id = 1
    update_data = {
        "name": "",
    }
    response = await async_client.patch(f"/categories/{category_id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_category_valid(async_client: AsyncClient):
    category_id = 1
    update_data = {
        "name": "Updated Category",
    }
    response = await async_client.patch(f"/categories/{category_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_category_not_found(async_client: AsyncClient):
    category_id = 9999
    response = await async_client.delete(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_category(async_client: AsyncClient):
    category_id = 1
    response = await async_client.delete(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_200_OK
