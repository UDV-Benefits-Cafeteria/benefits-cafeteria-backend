import pytest
from fastapi import status
from httpx import AsyncClient

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
    response = await async_client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert created_user["firstname"] == user_data["firstname"]
    assert created_user["lastname"] == user_data["lastname"]


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


# # Test case for uploading users via Excel
# @pytest.mark.asyncio
# async def test_upload_users(async_client: AsyncClient):
#     # Create a sample Excel file
#     df = pd.DataFrame({
#         "email": ["test1@example.com", "test2@example.com"],
#         "имя": ["John", "Jane"],
#         "фамилия": ["Doe", "Doe"],
#         "отчество": ["Smith", "Emily"],
#         "роль": ["admin", "hr"],
#         "дата найма": ["10.10.2023", "11.10.2023"],
#         "адаптационный период": [True, False],
#         "ю-коины": [100, 50],
#         "должность": ["employee", "hr"],
#         "юр. лицо": [None, None],
#     })
#     file_content = BytesIO()
#     df.to_excel(file_content, index=False)
#     file_content.seek(0)
#
#     files = {'file': ("users.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
#     response = await async_client.post("/users/upload", files=files)
#
#     assert response.status_code == status.HTTP_201_CREATED
#     upload_response = response.json()
#     assert len(upload_response["created_users"]) == 2
#     assert len(upload_response["errors"]) == 0
