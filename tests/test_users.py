import pytest
from fastapi import status
from httpx import AsyncClient
from src.utils.email import fm

# Test data
user_data = {
    "email": "test@example.com",
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

update_data = {
    "firstname": "Jane",
    "lastname": "Doe",
}


# Test case for creating a user
@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    fm.config.SUPPRESS_SEND = 1
    with fm.record_messages():
        response = await async_client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_user = response.json()
        assert created_user["email"] == user_data["email"]
        assert created_user["firstname"] == user_data["firstname"]
        assert created_user["lastname"] == user_data["lastname"]


# Test case for creating a user with missing required fields
@pytest.mark.asyncio
async def test_create_user_invalid(async_client: AsyncClient):
    invalid_user_data = {
        "email": "",  # Invalid email
        "firstname": "John",
        "lastname": "Doe",
        # Missing required fields, etc.
    }
    response = await async_client.post("/users/", json=invalid_user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test case for updating a user with invalid data
@pytest.mark.asyncio
async def test_update_user_invalid(async_client: AsyncClient):
    user_id = 1
    invalid_update_data = {
        "firstname": "",  # Invalid first name
        "lastname": "Doe",
    }
    response = await async_client.patch(f"/users/{user_id}", json=invalid_update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test case for updating a non-existent user
@pytest.mark.asyncio
async def test_update_user_not_found(async_client: AsyncClient):
    user_id = 999  # Assuming this user does not exist
    response = await async_client.patch(f"/users/{user_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Test case for updating a user
@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient):
    # Assuming user with id 1 exists
    user_id = 1
    response = await async_client.patch(f"/users/{user_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["firstname"] == update_data["firstname"]
    assert updated_user["lastname"] == update_data["lastname"]


# Test case for getting a user by ID
@pytest.mark.asyncio
async def test_get_user(async_client: AsyncClient):
    # Assuming user with id 1 exists
    user_id = 1
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    user = response.json()
    assert user["id"] == user_id
    assert user["email"] == "test@example.com"


# Test case for handling non-existent user
@pytest.mark.asyncio
async def test_get_user_not_found(async_client: AsyncClient):
    # Assuming user with id 999 does not exist
    user_id = 999
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Test case for uploading users with an invalid file type
@pytest.mark.asyncio
async def test_upload_users_invalid_file_type(async_client: AsyncClient):
    response = await async_client.post(
        "/users/upload", files={"file": ("test.txt", b"some content", "text/plain")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
