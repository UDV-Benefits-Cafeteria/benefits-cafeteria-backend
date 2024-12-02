import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.positions import PositionsService


@pytest.mark.asyncio
async def test_get_position_not_found(employee_client: AsyncClient):
    position_id = 9999
    response = await employee_client.get(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_position_valid(hr_client: AsyncClient):
    valid_position_data = {
        "name": "Software Engineer",
    }
    response = await hr_client.post("/positions/", json=valid_position_data)
    assert response.status_code == status.HTTP_201_CREATED
    position = response.json()
    assert "id" in position
    assert position["name"] == valid_position_data["name"].lower()

    position_in_db = await PositionsService().read_by_id(position["id"])

    assert position_in_db.id == position["id"]


@pytest.mark.asyncio
async def test_create_position_invalid(hr_client: AsyncClient):
    invalid_position_data = {
        "name": "",
    }
    response = await hr_client.post("/positions/", json=invalid_position_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_position_not_found(hr_client: AsyncClient):
    position_id = 9999
    update_data = {
        "name": "Updated Position",
    }
    response = await hr_client.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_position_valid(hr_client: AsyncClient):
    position_data = {
        "name": "Original Position",
    }
    create_response = await hr_client.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    update_data = {
        "name": "Updated Position",
    }
    update_response = await hr_client.patch(
        f"/positions/{position_id}", json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_position = update_response.json()
    assert updated_position["name"] == update_data["name"].lower()

    position_in_db = await PositionsService().read_by_id(position_id)

    assert position_in_db.name == update_data["name"].lower()


@pytest.mark.asyncio
async def test_update_position_invalid(hr_client: AsyncClient):
    position_data = {
        "name": "Position to Update",
    }
    create_response = await hr_client.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    update_data = {
        "name": "",
    }
    response = await hr_client.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_positions(employee_client: AsyncClient):
    response = await employee_client.get("/positions/")
    assert response.status_code == status.HTTP_200_OK
    positions = response.json()
    assert isinstance(positions, list)


@pytest.mark.asyncio
async def test_delete_position_not_found(hr_client: AsyncClient):
    position_id = 9999
    response = await hr_client.delete(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_position(hr_client: AsyncClient):
    position_data = {
        "name": "Position to Delete",
    }
    create_response = await hr_client.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    delete_response = await hr_client.delete(f"/positions/{position_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await hr_client.get(f"/positions/{position_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_employee_cannot_create_position(employee_client: AsyncClient):
    position_data = {
        "name": "Unauthorized Position",
    }
    response = await employee_client.post("/positions/", json=position_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_unauthenticated_access(auth_client: AsyncClient):
    response = await auth_client.get("/positions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_position_lowercase(admin_client: AsyncClient):
    position_data = {
        "name": "UPPERCASE Position",
    }
    response = await admin_client.post("/positions/", json=position_data)
    position = response.json()
    assert position["name"] == position_data["name"].lower()

    # Test service method
    position_by_name = await PositionsService().read_by_name(
        position_data["name"].upper()
    )
    assert position_by_name is not None
