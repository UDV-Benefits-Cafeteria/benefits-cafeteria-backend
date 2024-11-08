import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_position_not_found(employee_client: AsyncClient):
    position_id = 9999
    response = await employee_client.get(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_position_valid(hr_client1: AsyncClient):
    valid_position_data = {
        "name": "Software Engineer",
    }
    response = await hr_client1.post("/positions/", json=valid_position_data)
    assert response.status_code == status.HTTP_201_CREATED
    position = response.json()
    assert "id" in position
    assert position["name"] == "Software Engineer"


@pytest.mark.asyncio
async def test_create_position_invalid(hr_client1: AsyncClient):
    invalid_position_data = {
        "name": "",
    }
    response = await hr_client1.post("/positions/", json=invalid_position_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_position_not_found(hr_client1: AsyncClient):
    position_id = 9999
    update_data = {
        "name": "Updated Position",
    }
    response = await hr_client1.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_position_valid(hr_client1: AsyncClient):
    position_data = {
        "name": "Original Position",
    }
    create_response = await hr_client1.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    update_data = {
        "name": "Updated Position",
    }
    update_response = await hr_client1.patch(
        f"/positions/{position_id}", json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_position = update_response.json()
    assert updated_position["name"] == "Updated Position"


@pytest.mark.asyncio
async def test_update_position_invalid(hr_client1: AsyncClient):
    position_data = {
        "name": "Position to Update",
    }
    create_response = await hr_client1.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    update_data = {
        "name": "",
    }
    response = await hr_client1.patch(f"/positions/{position_id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_positions(employee_client: AsyncClient):
    response = await employee_client.get("/positions/")
    assert response.status_code == status.HTTP_200_OK
    positions = response.json()
    assert isinstance(positions, list)


@pytest.mark.asyncio
async def test_delete_position_not_found(hr_client1: AsyncClient):
    position_id = 9999
    response = await hr_client1.delete(f"/positions/{position_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_position(hr_client1: AsyncClient):
    position_data = {
        "name": "Position to Delete",
    }
    create_response = await hr_client1.post("/positions/", json=position_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    position = create_response.json()
    position_id = position["id"]

    delete_response = await hr_client1.delete(f"/positions/{position_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await hr_client1.get(f"/positions/{position_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_employee_cannot_create_position(employee_client: AsyncClient):
    position_data = {
        "name": "Unauthorized Position",
    }
    response = await employee_client.post("/positions/", json=position_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_unauthenticated_access():
    from httpx import ASGITransport

    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as unauthenticated_client:
        response = await unauthenticated_client.get("/positions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
