import pytest
from fastapi import status
from httpx import AsyncClient

from src.utils.email import fm

requests_benefit_data = {
    "name": "DMS",
    "description": "Comprehensive health insurance for employees",
    "coins_cost": 5,
    "min_level_cost": 1,
}

requests_user_data = {
    "email": "testbenefitrequest@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "middlename": "Smith",
    "role": "admin",
    "hired_at": "2023-10-10",
    "is_adapted": True,
    "is_active": True,
    "is_verified": False,
    "coins": 100,
    "position_id": None,
    "legal_entity_id": None,
}


@pytest.mark.asyncio
async def test_create_benefit_request_valid(async_client: AsyncClient):
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():
        benefit = await async_client.post("/benefits/", json=requests_benefit_data)
        user = await async_client.post("/users/", json=requests_user_data)
        valid_benefit_request_data = {
            "benefit_id": benefit.json()["id"],
            "user_id": user.json()["id"],
        }
        response = await async_client.post(
            "/benefit-requests/", json=valid_benefit_request_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_benefit_request_invalid(async_client: AsyncClient):
    invalid_benefit_request_data = {"benefit_id": 9999, "user_id": 9999}
    response = await async_client.post(
        "/benefit-requests/", json=invalid_benefit_request_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_benefit_request_not_found(async_client: AsyncClient):
    request_id = 9999
    response = await async_client.get(f"/benefit-requests/{request_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_benefit_requests_by_user(async_client: AsyncClient):
    response = await async_client.get("/benefit-requests/user/1")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_benefit_request_not_found(async_client: AsyncClient):
    request_id = 9999
    update_data = {"comment": "Some test comment"}
    response = await async_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_benefit_request_invalid(async_client: AsyncClient):
    request_id = 1
    update_data = {"user_id": 555, "comment": "Some test comment"}
    response = await async_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_benefit_request_valid(async_client: AsyncClient):
    request_id = 1
    update_data = {"user_id": 1, "comment": "Some test comment"}
    response = await async_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_benefit_request_not_found(async_client: AsyncClient):
    request_id = 9999
    response = await async_client.delete(f"/benefit-requests/{request_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit_request(async_client: AsyncClient):
    request_id = 1
    response = await async_client.delete(f"/benefit-requests/{request_id}")
    assert response.status_code == status.HTTP_200_OK
