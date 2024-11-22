import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.legal_entities import LegalEntitiesService


@pytest.mark.asyncio
async def test_get_legal_entity_not_found(employee_client: AsyncClient):
    entity_id = 9999
    response = await employee_client.get(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_legal_entity_valid(hr_client: AsyncClient):
    valid_legal_entity_data = {
        "name": "Test Entity",
    }
    response = await hr_client.post("/legal-entities/", json=valid_legal_entity_data)
    assert response.status_code == status.HTTP_201_CREATED
    legal_entity = response.json()

    assert "id" in legal_entity
    assert legal_entity["name"] == "Test Entity"

    entity_in_db = await LegalEntitiesService().read_by_id(legal_entity["id"])
    assert entity_in_db is not None


@pytest.mark.asyncio
async def test_create_legal_entity_invalid(hr_client: AsyncClient):
    invalid_legal_entity_data = {
        "name": "",
    }
    response = await hr_client.post("/legal-entities/", json=invalid_legal_entity_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_legal_entity_not_found(hr_client: AsyncClient):
    entity_id = 9999
    update_data = {
        "name": "Updated Name",
    }
    response = await hr_client.patch(f"/legal-entities/{entity_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_legal_entity_valid(hr_client: AsyncClient):
    legal_entity_data = {
        "name": "Original Entity",
    }
    create_response = await hr_client.post("/legal-entities/", json=legal_entity_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    legal_entity = create_response.json()
    entity_id = legal_entity["id"]

    update_data = {
        "name": "Updated Entity",
    }
    update_response = await hr_client.patch(
        f"/legal-entities/{entity_id}", json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_entity = update_response.json()

    assert updated_entity["name"] == "Updated Entity"

    response = await hr_client.get(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == "Updated Entity"

    entity_in_db = await LegalEntitiesService().read_by_id(entity_id)

    assert entity_in_db.name == "Updated Entity"


@pytest.mark.asyncio
async def test_update_legal_entity_invalid(hr_client: AsyncClient):
    legal_entity_data = {
        "name": "Entity to Update",
    }
    create_response = await hr_client.post("/legal-entities/", json=legal_entity_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    legal_entity = create_response.json()
    entity_id = legal_entity["id"]

    update_data = {
        "name": "",
    }
    response = await hr_client.patch(f"/legal-entities/{entity_id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_legal_entities(employee_client: AsyncClient):
    response = await employee_client.get("/legal-entities/")
    assert response.status_code == status.HTTP_200_OK
    legal_entities = response.json()
    assert isinstance(legal_entities, list)


@pytest.mark.asyncio
async def test_delete_legal_entity_not_found(hr_client: AsyncClient):
    entity_id = 9999
    response = await hr_client.delete(f"/legal-entities/{entity_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_legal_entity_valid(hr_client: AsyncClient):
    legal_entity_data = {
        "name": "Entity to Delete",
    }
    create_response = await hr_client.post("/legal-entities/", json=legal_entity_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    legal_entity = create_response.json()
    entity_id = legal_entity["id"]

    delete_response = await hr_client.delete(f"/legal-entities/{entity_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await hr_client.get(f"/legal-entities/{entity_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_employee_cannot_create_legal_entity(employee_client: AsyncClient):
    legal_entity_data = {
        "name": "Unauthorized Entity",
    }
    response = await employee_client.post("/legal-entities/", json=legal_entity_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_unauthenticated_access_legal_entities(auth_client):
    response = await auth_client.get("/legal-entities/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
