from io import BytesIO
from typing import Any, BinaryIO, Optional

import pandas as pd
import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.exceptions import EntityNotFoundError
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

    legal_entity_in_db = await LegalEntitiesService().read_by_id(legal_entity["id"])
    assert legal_entity_in_db is not None


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

    legal_entity_in_db = await LegalEntitiesService().read_by_id(entity_id)

    assert legal_entity_in_db.name == "Updated Entity"


@pytest.mark.asyncio
async def test_update_legal_entity_invalid(hr_client: AsyncClient, legal_entity1a):
    update_data = {
        "name": "",
    }
    response = await hr_client.patch(
        f"/legal-entities/{legal_entity1a.id}", json=update_data
    )
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


async def test_get_legal_entity_case_sensitive(admin_client: AsyncClient):
    legal_entity_data = {
        "name": "UPPERCASE LEGAL ENTITY",
    }
    response = await admin_client.post("/legal-entities/", json=legal_entity_data)
    legal_entity = response.json()
    assert legal_entity["name"] != legal_entity_data["name"].lower()

    # Test service method
    with pytest.raises(EntityNotFoundError):
        await LegalEntitiesService().read_by_name(legal_entity_data["name"].lower())

    legal_entity_by_name = await LegalEntitiesService().read_by_name(
        legal_entity_data["name"]
    )
    assert legal_entity_by_name is not None


@pytest.mark.asyncio
async def test_unauthenticated_access_legal_entities(auth_client: AsyncClient):
    response = await auth_client.get("/legal-entities/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Testing EXCEL for legal entities


# Helper function for creating Excel file
def create_excel_file_legal_entities(
    rows: list[dict[str, Any]],
    sheet_name: str = "LegalEntities",
    columns_input: Optional[list[str]] = None,
) -> bytes:
    columns = columns_input or ["название"]
    df = pd.DataFrame(rows, columns=columns)
    excel_file: BinaryIO = BytesIO()
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    excel_file.seek(0)
    return excel_file.read()


@pytest.mark.excel
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "upload_and_create_success",
            "rows": [
                {"название": "Legal Entity A"},
                {"название": "Legal Entity B"},
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_entities_count": 2,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_entities_count": 2,
            "bulk_errors_count": 0,
        },
        {
            "name": "upload_empty_data",
            "rows": [
                {"название": ""},
                {},
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_entities_count": 0,
            "errors_count": 0,
            "bulk_create_status_code": None,
            "created_entities_count": None,
            "bulk_errors_count": None,
        },
        {
            "name": "upload_partial_success",
            "rows": [
                {"название": "Legal Entity A"},
                {"название": "B"},  # Invalid data
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_entities_count": 1,
            "errors_count": 1,
            "bulk_create_status_code": 201,
            "created_entities_count": 1,
            "bulk_errors_count": 0,
        },
        {
            "name": "upload_duplicate_data",
            "rows": [
                {"название": "Legal Entity A"},
                {"название": "Legal Entity B"},
                {"название": "Legal Entity C"},
                {"название": "Legal Entity A"},
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_entities_count": 3,
            "errors_count": 1,  # One duplicate
            "bulk_create_status_code": 201,
            "created_entities_count": 3,
            "bulk_errors_count": 0,
        },
        {
            "name": "upload_existing_data",
            "rows": [
                {"название": "Legal Entity New"},
                {"название": "Legal Entity 2b"},  # Existing legal entity
                {"название": "Legal Entity New2"},
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_entities_count": 2,
            "errors_count": 1,
            "bulk_create_status_code": 201,
            "created_entities_count": 2,
            "bulk_errors_count": 0,
        },
    ],
)
async def test_upload_legal_entities(hr_client: AsyncClient, test_case, legal_entity2b):
    file_name = "test_legal_entities.xlsx"
    file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    excel_content = create_excel_file_legal_entities(
        rows=test_case["rows"],
        columns_input=test_case.get("columns_input"),
    )

    files = {
        "file": (
            file_name,
            excel_content,
            file_type,
        )
    }

    upload_response = await hr_client.post("/legal-entities/upload", files=files)

    assert (
        upload_response.status_code == test_case["upload_status_code"]
    ), f"Test '{test_case['name']}' failed on upload step"

    if test_case["upload_status_code"] == status.HTTP_200_OK:
        upload_data = upload_response.json()

        assert (
            len(upload_data.get("valid_entities", []))
            == test_case["valid_entities_count"]
        ), f"Test '{test_case['name']}' failed: expected {test_case['valid_entities_count']} valid entities, got {len(upload_data.get('valid_entities', []))}"
        assert (
            len(upload_data.get("errors", [])) == test_case["errors_count"]
        ), f"Test '{test_case['name']}' failed: expected {test_case['errors_count']} errors, got {len(upload_data.get('errors', []))}"

        if test_case["valid_entities_count"] > 0:
            bulk_create_response = await hr_client.post(
                "/legal-entities/bulk_create", json=upload_data["valid_entities"]
            )

            assert (
                bulk_create_response.status_code == test_case["bulk_create_status_code"]
            ), f"Test '{test_case['name']}' failed on bulk_create step"

            bulk_create_data = bulk_create_response.json()
            assert (
                len(bulk_create_data["created_entities"])
                == test_case["created_entities_count"]
            ), f"Test '{test_case['name']}' failed: expected {test_case['created_entities_count']} created entities, got {len(bulk_create_data['created_entities'])}"

            entity = await LegalEntitiesService().read_by_id(
                bulk_create_data["created_entities"][0]["id"]
            )

            assert entity is not None

            assert (
                len(bulk_create_data["errors"]) == test_case["bulk_errors_count"]
            ), f"Test '{test_case['name']}' failed: expected {test_case['bulk_errors_count']} bulk_create errors, got {len(bulk_create_data['errors'])}"


@pytest.mark.excel
@pytest.mark.asyncio
async def test_upload_legal_entities_wrong_column(hr_client: AsyncClient):
    missing_columns = ["wrong_column"]  # Wrong column provided
    entity_rows = [
        {"название": "Legal Entity A"},
    ]

    excel_content = create_excel_file_legal_entities(
        rows=entity_rows, columns_input=missing_columns
    )

    files = {
        "file": (
            "missing_columns.xlsx",
            excel_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    upload_response = await hr_client.post("/legal-entities/upload", files=files)

    assert upload_response.status_code == status.HTTP_400_BAD_REQUEST

    assert "Column for 'name' might be missing" in upload_response.json()["detail"]


@pytest.mark.excel
@pytest.mark.asyncio
async def test_upload_legal_entities_invalid_file_type(hr_client: AsyncClient):
    file_content = "Not an Excel file."

    files = {"file": ("not_excel.txt", file_content, "text/plain")}
    response = await hr_client.post("/legal-entities/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"] == "Invalid file type. Please upload an Excel file."
    )
