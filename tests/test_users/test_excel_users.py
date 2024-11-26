from datetime import date, timedelta
from io import BytesIO
from typing import Any, BinaryIO, Optional

import pandas as pd
import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.users import UsersService


def create_excel_file(
    rows: list[dict[str, Any]],
    sheet_name: str = "Users",
    columns_input: Optional[list[str]] = None,
) -> bytes:
    columns = columns_input or [
        "email",
        "имя",
        "фамилия",
        "роль",
        "дата найма",
        "адаптационный период",
        "отчество",
        "ю-коины",
        "должность",
        "юр. лицо",
    ]

    df = pd.DataFrame(rows, columns=columns)
    excel_file: BinaryIO = BytesIO()
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    excel_file.seek(0)
    return excel_file.read()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "upload_and_create_success",
            "rows": [
                {
                    "email": "exceluser1@example.com",
                    "фамилия": "Иванов",
                    "имя": "Иван",
                    "отчество": "Иванович",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    "адаптационный период": "да",
                    "ю-коины": 100,
                },
                {
                    "email": "exceluser2@example.com",
                    "фамилия": "Петров",
                    "имя": "Петр",
                    "отчество": "Петрович",
                    "роль": "hr",
                    "юр. лицо": "Legal Entity 1a",
                    "дата найма": (date.today() - timedelta(days=30)).isoformat(),
                    "адаптационный период": "нет",
                    "ю-коины": 200,
                },
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_users_count": 2,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_users_count": 2,
            "bulk_errors_count": 0,
        },
        {
            "name": "upload_invalid_data",
            "rows": [
                {
                    "email": "invaliduser@example.com",
                    "фамилия": "",  # Empty string
                    "имя": "Анна",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    # No email
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "invaliduser2@example.com",
                    "фамилия": "Абрамов",
                    "имя": "Абрам",
                    "роль": "qwertyuiop",  # Invalid role
                    "дата найма": date.today().isoformat(),
                },
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 3,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "upload_partial_success",
            "rows": [
                {
                    "email": "validuser@example.com",
                    "фамилия": "Николаев",
                    "имя": "Николай",
                    "отчество": "Николаевич",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    "адаптационный период": "нет",
                    "ю-коины": 150,
                },
                {
                    "email": "invaliduserdata@example.com",
                    "фамилия": "Марьева",
                    "имя": "Мария123",  # Invalid data in name
                    "роль": "hr",
                    "дата найма": "2021-01-01",
                },
            ],
            "columns_input": None,
            "upload_status_code": 200,
            "valid_users_count": 1,
            "errors_count": 1,
            "bulk_create_status_code": 201,
            "created_users_count": 1,
            "bulk_errors_count": 0,
        },
        {
            "name": "different_column_variants",
            "rows": [
                {
                    "электронная почта": "user1@example.com",
                    "фамилия": "Иванов",
                    "имя": "Иван",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "электронная почта": "user2@example.com",
                    "фамилия": "Петров",
                    "имя": "Петр",
                    "роль": "hr",
                    "дата найма": date.today().isoformat(),
                    "юкоины": 999,
                },
            ],
            "columns_input": [
                "электронная почта",
                "фамилия",
                "имя",
                "роль",
                "дата найма",
                "юкоины",
            ],
            "upload_status_code": 200,
            "valid_users_count": 2,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_users_count": 2,
            "bulk_errors_count": 0,
        },
        {
            "name": "missing_required_fields",
            "rows": [
                {
                    # Missing 'email'
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "user@example.com",
                    # Missing 'lastname'
                    "имя": "Мария",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "user2@example.com",
                    "фамилия": "Иванов",
                    # Missing 'firstname'
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "user3@example.com",
                    "фамилия": "Петров",
                    "имя": "Петр",
                    # Missing 'role'
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "user4@example.com",
                    "фамилия": "Смирнов",
                    "имя": "Игорь",
                    "роль": "employee",
                    # Missing 'дата найма'
                },
            ],
            "columns_input": ["email", "фамилия", "имя", "роль", "дата найма"],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 5,  # One error per row
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "optional_fields",
            "rows": [
                {
                    "email": "user@example.com",
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    # No optional fields
                }
            ],
            "columns_input": ["email", "фамилия", "имя", "роль", "дата найма"],
            "upload_status_code": 200,
            "valid_users_count": 1,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_users_count": 1,
            "bulk_errors_count": 0,
        },
        {
            "name": "invalid_is_adapted_field",
            "rows": [
                {
                    "email": "user@example.com",
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    "адаптационный период": "maybe",  # Invalid value
                }
            ],
            "columns_input": [
                "email",
                "фамилия",
                "имя",
                "роль",
                "дата найма",
                "адаптационный период",
            ],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "invalid_role",
            "rows": [
                {
                    "email": "user@example.com",
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "manager",  # Invalid role
                    "дата найма": date.today().isoformat(),
                }
            ],
            "columns_input": ["email", "фамилия", "имя", "роль", "дата найма"],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "nonexistent_position",
            "rows": [
                {
                    "email": "user@example.com",
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    "должность": "Неизвестная должность",
                }
            ],
            "columns_input": [
                "email",
                "фамилия",
                "имя",
                "роль",
                "дата найма",
                "должность",
            ],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "nonexistent_legal_entity",
            "rows": [
                {
                    "email": "user@example.com",
                    "фамилия": "Сидоров",
                    "имя": "Сидор",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                    "юр. лицо": "Неизвестное юр. лицо",
                }
            ],
            "columns_input": [
                "email",
                "фамилия",
                "имя",
                "роль",
                "дата найма",
                "юр. лицо",
            ],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
        {
            "name": "duplicate_emails_in_file",
            "rows": [
                {
                    "email": "duplicate@example.com",
                    "фамилия": "Иванов",
                    "имя": "Иван",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
                {
                    "email": "duplicate@example.com",  # Duplicate email in the file
                    "фамилия": "Петров",
                    "имя": "Петр",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                },
            ],
            "columns_input": ["email", "фамилия", "имя", "роль", "дата найма"],
            "upload_status_code": 200,
            "valid_users_count": 2,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_users_count": 1,
            "bulk_errors_count": 1,  # Expected error in bulk create
        },
        {
            "name": "existing_email_in_db",
            "rows": [
                {
                    "email": "hr1@example.com",  # email exists in DB
                    "фамилия": "Новиков",
                    "имя": "Николай",
                    "роль": "employee",
                    "дата найма": date.today().isoformat(),
                }
            ],
            "columns_input": ["email", "фамилия", "имя", "роль", "дата найма"],
            "upload_status_code": 200,
            "valid_users_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_users_count": 0,
            "bulk_errors_count": 0,
        },
    ],
)
async def test_upload_users(hr_client: AsyncClient, test_case, legal_entity1a):
    file_name = f"{test_case['name']}.xlsx"
    file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    excel_content = create_excel_file(
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

    upload_response = await hr_client.post("/users/upload", files=files)

    assert (
        upload_response.status_code == test_case["upload_status_code"]
    ), f"Test '{test_case['name']}' failed on upload step"

    if test_case["upload_status_code"] == 200:
        upload_data = upload_response.json()

        assert (
            len(upload_data.get("valid_users", [])) == test_case["valid_users_count"]
        ), f"Test '{test_case['name']}' failed: expected {test_case['valid_users_count']} valid users, got {len(upload_data.get('valid_users', []))}"
        assert (
            len(upload_data.get("errors", [])) == test_case["errors_count"]
        ), f"Test '{test_case['name']}' failed: expected {test_case['errors_count']} errors, got {len(upload_data.get('errors', []))}"

        if test_case["valid_users_count"] > 0:
            bulk_create_response = await hr_client.post(
                "/users/bulk_create", json=upload_data["valid_users"]
            )

            assert (
                bulk_create_response.status_code == test_case["bulk_create_status_code"]
            ), f"Test '{test_case['name']}' failed on bulk_create step"

            bulk_create_data = bulk_create_response.json()
            assert (
                len(bulk_create_data["created_users"])
                == test_case["created_users_count"]
            ), f"Test '{test_case['name']}' failed: expected {test_case['created_users_count']} created users, got {len(bulk_create_data['created_users'])}"

            user_service = UsersService()

            for created_user in bulk_create_data["created_users"]:
                user = await user_service.read_by_id(created_user["id"])
                assert user is not None

            assert (
                len(bulk_create_data["errors"]) == test_case["bulk_errors_count"]
            ), f"Test '{test_case['name']}' failed: expected {test_case['bulk_errors_count']} bulk_create errors, got {len(bulk_create_data['errors'])}"


@pytest.mark.asyncio
async def test_upload_users_missing_columns(hr_client: AsyncClient):
    missing_columns = [
        "имя",
        "фамилия",
        "роль",
        "дата найма",
        "адаптационный период",
        "отчество",
        "ю-коины",
        "должность",
        "юр. лицо",
    ]
    user_rows = [
        {
            "фамилия": "Кузнецов",
            "имя": "Кузьма",
            "роль": "employee",
            "дата найма": date.today().isoformat(),
        },
    ]

    excel_content = create_excel_file(rows=user_rows, columns_input=missing_columns)

    files = {
        "file": (
            "missing_columns.xlsx",
            excel_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    upload_response = await hr_client.post("/users/upload", files=files)

    assert upload_response.status_code == status.HTTP_400_BAD_REQUEST

    assert "Error while parsing users" in upload_response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_users_invalid_file_type(hr_client: AsyncClient):
    file_content = "Not an Excel file."

    files = {"file": ("not_excel.txt", file_content, "text/plain")}
    response = await hr_client.post("/users/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"] == "Invalid file type. Please upload an Excel file."
    )
