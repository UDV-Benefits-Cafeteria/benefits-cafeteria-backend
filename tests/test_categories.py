import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.categories import CategoriesService


@pytest.mark.asyncio
async def test_create_category_valid(admin_client: AsyncClient):
    category_data = {
        "name": "New Category",
    }
    response = await admin_client.post("/categories/", json=category_data)
    assert response.status_code == status.HTTP_201_CREATED
    category = response.json()
    assert category["name"] == category_data["name"].lower()
    category_in_db = await CategoriesService().read_by_id(category["id"])
    assert category_in_db is not None


@pytest.mark.asyncio
async def test_create_category_invalid(admin_client: AsyncClient):
    invalid_category_data = {
        "name": "",
    }
    response = await admin_client.post("/categories/", json=invalid_category_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_category(admin_client: AsyncClient, category):
    response = await admin_client.get(f"/categories/{category.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category.id
    assert data["name"] == category.name.lower()


@pytest.mark.asyncio
async def test_get_category_not_found(admin_client: AsyncClient):
    category_id = 9999
    response = await admin_client.get(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_categories(admin_client: AsyncClient):
    response = await admin_client.get("/categories/")
    assert response.status_code == status.HTTP_200_OK
    categories = response.json()
    assert isinstance(categories, list)


@pytest.mark.asyncio
async def test_update_category_not_found(admin_client: AsyncClient):
    category_id = 9999
    update_data = {
        "name": "Updated Category",
    }
    response = await admin_client.patch(f"/categories/{category_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_category_invalid(admin_client: AsyncClient, category):
    update_data = {
        "name": "",
    }
    response = await admin_client.patch(f"/categories/{category.id}", json=update_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_category_valid(admin_client: AsyncClient, category):
    update_data = {"name": "Updated Category Name"}
    response = await admin_client.patch(f"/categories/{category.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK

    updated_category = response.json()
    assert updated_category["name"] == update_data["name"].lower()

    category_in_db = await CategoriesService().read_by_id(updated_category["id"])
    assert category_in_db is not None

    response = await admin_client.get(f"/categories/{category.id}")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == update_data["name"].lower()


@pytest.mark.asyncio
async def test_delete_category_not_found(admin_client: AsyncClient):
    category_id = 9999
    response = await admin_client.delete(f"/categories/{category_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_category(admin_client: AsyncClient):
    category_data = {"name": "Category to Delete"}
    create_response = await admin_client.post("/categories/", json=category_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    category = create_response.json()

    delete_response = await admin_client.delete(f"/categories/{category['id']}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await admin_client.get(f"/categories/{category['id']}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_employee_cannot_create_category(employee_client: AsyncClient):
    category_data = {
        "name": "Unauthorized Category",
    }
    response = await employee_client.post("/categories/", json=category_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_category_lowercase(admin_client: AsyncClient):
    category_data = {
        "name": "UPPERCASE Category",
    }
    response = await admin_client.post("/categories/", json=category_data)
    category = response.json()
    assert category["name"] == category_data["name"].lower()

    # Test service method
    category_by_name = await CategoriesService().read_by_name(
        category_data["name"].upper()
    )
    assert category_by_name is not None
