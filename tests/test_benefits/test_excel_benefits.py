from io import BytesIO
from typing import Any, BinaryIO, Optional

import pandas as pd
import pytest
from fastapi import status
from httpx import AsyncClient


def create_excel_file(
    rows: list[dict[str, Any]],
    sheet_name: str = "Users",
    columns_input: Optional[list[str]] = None,
) -> bytes:
    columns = columns_input or [
        "name",
        "coins_cost",
        "min_level_cost",
        "adaptation_required",
        "is_active",
        "description",
        "real_currency_cost",
        "amount",
        "is_fixed_period",
        "usage_limit",
        "usage_period_days",
        "period_start_date",
        "available_from",
        "available_by",
        "category_name",
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
            "name": "valid_benefit_data",
            "rows": [
                {
                    "name": "Benefit A",
                    "coins_cost": 100,
                    "min_level_cost": 50,
                    "adaptation_required": True,
                    "is_active": True,
                    "description": "Valid benefit",
                    "real_currency_cost": 1000,
                    "amount": 10,
                    "category_name": "Category A",
                },
            ],
            "columns_input": [
                "name",
                "coins_cost",
                "min_level_cost",
                "adaptation_required",
                "is_active",
                "description",
                "real_currency_cost",
                "amount",
                "category_name",
            ],
            "upload_status_code": 200,
            "valid_benefits_count": 1,
            "errors_count": 0,
            "bulk_create_status_code": 201,
            "created_benefits_count": 1,
            "bulk_errors_count": 0,
        },
        {
            "name": "missing_columns",
            "rows": [
                {
                    "coins_cost": 100,
                    "min_level_cost": 50,
                    # Missing 'name'
                },
            ],
            "columns_input": ["coins_cost", "min_level_cost"],
            "upload_status_code": 400,
            "valid_benefits_count": 0,
            "errors_count": 1,
            "bulk_create_status_code": None,
            "created_benefits_count": None,
            "bulk_errors_count": None,
        },
        {
            "name": "valid_and_invalid_data",
            "rows": [
                {
                    "name": "Benefit A",
                    "coins_cost": 100,  # Valid coins cost
                    "min_level_cost": 50,
                },
                {
                    "name": "Benefit B",
                    "coins_cost": -100,  # Invalid coins cost
                    "min_level_cost": 50,
                },
            ],
            "columns_input": [
                "name",
                "coins_cost",
                "min_level_cost",
            ],
            "upload_status_code": 200,
            "valid_benefits_count": 1,
            "errors_count": 1,
            "bulk_create_status_code": 201,
            "created_benefits_count": 1,
            "bulk_errors_count": 0,
        },
    ],
)
async def test_upload_benefits(hr_client: AsyncClient, test_case, legal_entity1a):
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

    upload_response = await hr_client.post("/benefits/upload", files=files)

    assert upload_response.status_code == test_case["upload_status_code"]

    if test_case["upload_status_code"] == 200:
        upload_data = upload_response.json()

        assert (
            len(upload_data.get("valid_benefits", []))
            == test_case["valid_benefits_count"]
        )

        assert len(upload_data.get("errors", [])) == test_case["errors_count"]

        if test_case["valid_benefits_count"] > 0:
            bulk_create_response = await hr_client.post(
                "/benefits/bulk_create", json=upload_data["valid_benefits"]
            )

            assert (
                bulk_create_response.status_code == test_case["bulk_create_status_code"]
            )

            bulk_create_data = bulk_create_response.json()

            assert (
                len(bulk_create_data["created_benefits"])
                == test_case["created_benefits_count"]
            )

            assert len(bulk_create_data["errors"]) == test_case["bulk_errors_count"]


@pytest.mark.asyncio
async def test_upload_benefits_invalid_file_type(hr_client: AsyncClient):
    file_content = "Not an Excel file."

    files = {"file": ("not_excel.txt", file_content, "text/plain")}
    response = await hr_client.post("/benefits/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"] == "Invalid file type. Please upload an Excel file."
    )
