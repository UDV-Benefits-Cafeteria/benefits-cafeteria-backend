import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_position_not_found(async_client: AsyncClient):
    position_id = 9999
    response = await async_client.get(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_position_valid(async_client: AsyncClient):
    valid_position_data = {
        "name": "Software Engineer",
    }
    response = await async_client.post("/positions/", json=valid_position_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_create_position_invalid(async_client: AsyncClient):
    invalid_position_data = {
        "name": "",
    }
    response = await async_client.post("/positions/", json=invalid_position_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_position_not_found(async_client: AsyncClient):
    position_id = 9999
    update_data = {
        "name": "Updated Position",
    }
    response = await async_client.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_position_valid(async_client: AsyncClient):
    position_id = 1
    update_data = {
        "name": "Updated Position",
    }
    response = await async_client.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_position_invalid(async_client: AsyncClient):
    position_id = 1
    update_data = {
        "name": "",
    }
    response = await async_client.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_positions(async_client: AsyncClient):
    response = await async_client.get("/positions/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_position_not_found(async_client: AsyncClient):
    position_id = 9999
    response = await async_client.delete(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_position(async_client: AsyncClient):
    position_id = 1
    response = await async_client.delete(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_200_OK
