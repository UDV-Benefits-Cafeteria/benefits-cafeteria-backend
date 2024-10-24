import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_legal_entity_not_found(async_client: AsyncClient):
    entity_id = 9999
    response = await async_client.get(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_legal_entity_valid(async_client: AsyncClient):
    valid_legal_entity_data = {
        "name": "Test Entity",
    }
    response = await async_client.post("/legal-entities/", json=valid_legal_entity_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_create_legal_entity_invalid(async_client: AsyncClient):
    invalid_legal_entity_data = {
        "name": "",
    }
    response = await async_client.post(
        "/legal-entities/", json=invalid_legal_entity_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_legal_entity_not_found(async_client: AsyncClient):
    entity_id = 9999
    update_data = {
        "name": "Updated Name",
    }
    response = await async_client.patch(
        f"/legal-entities/{entity_id}", json=update_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_legal_entity_valid(async_client: AsyncClient):
    entity_id = 1
    update_data = {
        "name": "Updated Name",
    }
    response = await async_client.patch(
        f"/legal-entities/{entity_id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_legal_entity_invalid(async_client: AsyncClient):
    entity_id = 1
    update_data = {
        "name": "",
    }
    response = await async_client.patch(
        f"/legal-entities/{entity_id}", json=update_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_legal_entities(async_client: AsyncClient):
    response = await async_client.get("/legal-entities/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_legal_entity_not_found(async_client: AsyncClient):
    entity_id = 9999
    response = await async_client.delete(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_legal_entity_valid(async_client: AsyncClient):
    entity_id = 1
    response = await async_client.delete(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_200_OK
