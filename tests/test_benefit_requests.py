from datetime import date
from typing import Optional

import pytest
from fastapi import status
from httpx import AsyncClient

import src.schemas.benefit as benefit_schemas
import src.schemas.request as schemas
import src.schemas.user as user_schemas
from src.models import BenefitRequest, LegalEntity, User
from src.services.benefits import BenefitsService
from src.services.users import UsersService
from src.utils.parser.excel_parser import ExcelParser
from tests.conftest import get_employee_client


async def create_test_benefit(benefit_data: dict) -> dict:
    valid_benefit_data = benefit_schemas.BenefitCreate.model_validate(benefit_data)

    created_benefit = await BenefitsService().create(valid_benefit_data)

    created_benefit_data = created_benefit.model_dump()
    assert created_benefit_data["id"] is not None

    return created_benefit_data


async def create_test_user(user_data: dict, executing_user: User) -> dict:
    admin_user_data = user_schemas.UserRead.model_validate(executing_user)

    valid_user_data = user_schemas.UserCreate.model_validate(user_data)

    created_user = await UsersService().create(valid_user_data, admin_user_data)

    created_user_data = created_user.model_dump()
    assert created_user_data["id"] is not None

    return created_user_data


async def perform_benefit_request_test(
    admin_user: User,
    benefit_data: dict,
    user_data: dict,
    expected_status: int,
) -> dict:
    # Create Benefit
    created_benefit_data = await create_test_benefit(benefit_data)

    # Create User
    created_user_data = await create_test_user(user_data, admin_user)

    # Authenticate as created user
    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
    }

    response = await employee_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == expected_status

    return {
        "benefit_request": response.json(),
        "user": created_user_data,
        "benefit": created_benefit_data,
    }


@pytest.mark.parametrize(
    "invalid_data, expected_status",
    [
        # Missing benefit_id
        (
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Invalid benefit_id type
        (
            {"benefit_id": "invalid_id"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        # Benefit does not exist
        (
            {"benefit_id": 9999},
            status.HTTP_404_NOT_FOUND,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_invalid_data(
    invalid_data, expected_status, employee_client: AsyncClient
):
    response = await employee_client.post("/benefit-requests/", json=invalid_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "benefit_data, user_data",
    [
        # Test 1
        (
            {
                "name": "Benefit Adapted User",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": True,
            },
            {
                "email": "adapted_user@example.com",
                "firstname": "Adapted",
                "lastname": "User",
                "role": "employee",
                "coins": 20,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
        ),
        # Test 2
        (
            {
                "name": "Benefit High Level",
                "coins_cost": 15,
                "min_level_cost": 2,
                "amount": 5,
                "adaptation_required": True,
            },
            {
                "email": "high_level_user@example.com",
                "firstname": "High",
                "lastname": "Level",
                "role": "employee",
                "coins": 15,
                "hired_at": "2021-01-01",
                "is_adapted": True,
            },
        ),
        # Test 3
        (
            {
                "name": "Benefit Non-Adapted User",
                "coins_cost": 5,
                "min_level_cost": 2,
                "amount": 8,
                "adaptation_required": False,
            },
            {
                "email": "non_adapted_user@example.com",
                "firstname": "NonAdapted",
                "lastname": "User",
                "role": "employee",
                "coins": 10,
                "hired_at": "2020-01-01",
                "is_adapted": False,
            },
        ),
        # Test 4
        (
            {
                "name": "Benefit Adapted Enough Coins",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "adapted_enough_coins_user@example.com",
                "firstname": "AdaptedCoins",
                "lastname": "User",
                "role": "employee",
                "coins": 10,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_request_pairwise(
    benefit_data: dict, user_data: dict, admin_user: User
):
    test_data = await perform_benefit_request_test(
        admin_user, benefit_data, user_data, status.HTTP_201_CREATED
    )

    benefit_request = test_data["benefit_request"]
    user = test_data["user"]
    benefit = test_data["benefit"]

    assert benefit_request["status"] == "pending"
    assert benefit_request["user"]["id"] == user["id"]
    assert benefit_request["benefit"]["id"] == benefit["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "benefit_data, user_data, expected_status",
    [
        # Test 1: User does not have enough coins
        (
            {
                "name": "Benefit High Cost",
                "coins_cost": 20,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "user_insufficient_coins@example.com",
                "firstname": "Insufficient",
                "lastname": "Coins",
                "role": "employee",
                "coins": 10,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 2: User does not have minimal required level
        (
            {
                "name": "Benefit High Level",
                "coins_cost": 10,
                "min_level_cost": 12,
                "amount": 10,
                "adaptation_required": False,
            },
            {
                "email": "user_low_level@example.com",
                "firstname": "Low",
                "lastname": "Level",
                "role": "employee",
                "coins": 20,
                "hired_at": date.today(),
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 3: User is not adapted and the benefit is requiring adaptation
        (
            {
                "name": "Benefit Requires Adaptation",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 10,
                "adaptation_required": True,
            },
            {
                "email": "user_not_adapted@example.com",
                "firstname": "NotAdapted",
                "lastname": "User",
                "role": "employee",
                "coins": 20,
                "hired_at": "2022-01-01",
                "is_adapted": False,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        # Test 4: Not enough amount of benefits
        (
            {
                "name": "Benefit Out of Stock",
                "coins_cost": 10,
                "min_level_cost": 1,
                "amount": 0,
                "adaptation_required": False,
            },
            {
                "email": "user_benefit_amount_insufficient@example.com",
                "firstname": "Benefit",
                "lastname": "AmountInsufficient",
                "role": "employee",
                "coins": 20,
                "hired_at": "2022-01-01",
                "is_adapted": True,
            },
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
async def test_benefit_request_invalid_conditions(
    admin_user: User,
    benefit_data: dict,
    user_data: dict,
    expected_status: int,
):
    await perform_benefit_request_test(
        admin_user=admin_user,
        benefit_data=benefit_data,
        user_data=user_data,
        expected_status=expected_status,
    )


@pytest.mark.request_with_status("pending", 444)
@pytest.mark.asyncio
async def test_update_benefit_request_pending_to_declined(
    hr_client: AsyncClient, benefit_request: BenefitRequest
):
    update_data = {"status": "declined"}

    response = await hr_client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK

    updated_request = response.json()
    assert updated_request["status"] == "declined"


# User with id = 333 has legal entity = 222 and hr_user has legal entity = 111, so the operation should fail
@pytest.mark.request_with_status("pending", 333)
@pytest.mark.asyncio
async def test_update_benefit_request_pending_to_declined_fail(
    hr_client: AsyncClient, benefit_request: BenefitRequest
):
    update_data = {"status": "declined"}

    response = await hr_client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.request_with_status("pending", 444)
@pytest.mark.asyncio
async def test_update_benefit_request_pending_and_add_performer_id(
    hr_client: AsyncClient, benefit_request: BenefitRequest, hr_user: User
):
    assert benefit_request.performer_id is None

    update_data = {"status": "approved"}

    response = await hr_client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK

    updated_request = response.json()
    assert updated_request["status"] == "approved"

    assert updated_request["performer_id"] == hr_user.id


@pytest.mark.request_with_status("approved", 444)
@pytest.mark.asyncio
async def test_update_benefit_request_approved_should_fail(
    hr_client: AsyncClient, benefit_request: BenefitRequest
):
    update_data = {"status": "declined"}

    response = await hr_client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.request_with_status("pending", 444)
@pytest.mark.asyncio
async def test_update_benefit_request_pending_to_declined_user(
    employee_user: User, benefit_request: BenefitRequest
):
    client = await get_employee_client(employee_user.id)

    update_data = {"status": "declined"}

    response = await client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.request_with_status("processing", 444)
@pytest.mark.asyncio
async def test_update_benefit_request_processing_to_approved_user(
    employee_user: User, benefit_request: BenefitRequest
):
    client = await get_employee_client(employee_user.id)

    update_data = {"status": "approved"}

    response = await client.patch(
        f"/benefit-requests/{benefit_request.id}", json=update_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_cancel_benefit_request_restores_coins_and_amount(
    admin_user: User,
    legal_entity1a,
):
    benefit_data = {
        "name": "Benefit Cancel Test",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }

    user_data = {
        "email": "user_cancel_test@example.com",
        "firstname": "Cancel",
        "lastname": "Test",
        "role": "employee",
        "coins": 20,
        "hired_at": "2022-01-01",
        "is_adapted": True,
        "legal_entity_id": legal_entity1a.id,
    }

    created_benefit_data = await create_test_benefit(benefit_data)

    created_user_data = await create_test_user(user_data, admin_user)

    employee_client = await get_employee_client(created_user_data["id"])

    request_data = {
        "benefit_id": created_benefit_data["id"],
    }

    request_create_response = await employee_client.post(
        "/benefit-requests/", json=request_data
    )
    assert request_create_response.status_code == status.HTTP_201_CREATED

    benefit_request = request_create_response.json()

    request_id = benefit_request["id"]

    benefit_response = await BenefitsService().read_by_id(created_benefit_data["id"])
    updated_benefit_data = benefit_response.model_dump()
    user_response = await UsersService().read_by_id(created_user_data["id"])
    updated_user_data = user_response.model_dump()

    assert updated_benefit_data["amount"] == benefit_data["amount"] - 1
    assert updated_user_data["coins"] == user_data["coins"] - benefit_data["coins_cost"]

    update_data = {
        "status": "declined",
    }

    response = await employee_client.patch(
        f"/benefit-requests/{request_id}", json=update_data
    )
    with pytest.raises(KeyError):
        assert response.json()["detail"] is None

    assert response.status_code == status.HTTP_200_OK

    updated_request = response.json()
    assert updated_request["status"] == "declined"

    restored_benefit_response = await BenefitsService().read_by_id(
        created_benefit_data["id"]
    )

    restored_benefit_data = restored_benefit_response.model_dump()
    assert restored_benefit_data["amount"] == benefit_data["amount"]

    restored_user_response = await UsersService().read_by_id(created_user_data["id"])
    restored_user_data = restored_user_response.model_dump()

    assert restored_user_data["coins"] == user_data["coins"]


@pytest.mark.asyncio
async def test_benefit_request_transaction(
    admin_user: User, legal_entity1a: LegalEntity
):
    benefit_data = {
        "name": "Benefit Transaction Test",
        "coins_cost": 50,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }

    user_data = {
        "email": "user_transaction_test@example.com",
        "firstname": "Transaction",
        "lastname": "Test",
        "role": "employee",
        "coins": 10,  # Not Enough
        "hired_at": "2022-01-01",
        "is_adapted": True,
        "legal_entity_id": legal_entity1a.id,
    }
    created_benefit_data = await create_test_benefit(benefit_data)

    created_user_data = await create_test_user(user_data, admin_user)

    benefit_id = created_benefit_data["id"]
    user_id = created_user_data["id"]

    assert benefit_id is not None
    assert user_id is not None

    employee_client = await get_employee_client(user_id)

    request_data = {
        "benefit_id": benefit_id,
    }

    request_create_response = await employee_client.post(
        "/benefit-requests/", json=request_data
    )

    assert request_create_response.status_code == status.HTTP_400_BAD_REQUEST

    benefit_after_operation = await BenefitsService().read_by_id(benefit_id)
    # Check that amount didn't change meaning transaction had a rollback
    assert benefit_after_operation.amount == 5

    user_after_operation = await UsersService().read_by_id(user_id)
    assert user_after_operation.coins == 10


@pytest.mark.elastic
@pytest.mark.asyncio
async def test_benefit_request_transaction_elastic(
    admin_client: AsyncClient,
    admin_user: User,
    setup_indices,
):
    benefit_data = {
        "name": "Benefit Transaction Test",
        "coins_cost": 50,
        "min_level_cost": 1,
        "amount": 5,
        "adaptation_required": False,
    }
    benefit_response = await admin_client.post("/benefits/", json=benefit_data)

    assert benefit_response.status_code == status.HTTP_201_CREATED

    get_benefits_response = await admin_client.get("/benefits/")
    assert get_benefits_response.json()[0]["amount"] == 5

    benefit = benefit_response.json()

    benefit_id = benefit["id"]

    request_data = {
        "benefit_id": benefit_id,
    }

    # Admin has 0 coins which is not enough
    request_create_response = await admin_client.post(
        "/benefit-requests/", json=request_data
    )

    assert request_create_response.status_code == status.HTTP_400_BAD_REQUEST

    benefit_after_operation = await BenefitsService().read_by_id(benefit_id)
    # Check that amount didn't change meaning transaction had a rollback
    assert benefit_after_operation.amount == 5

    user_after_operation = await UsersService().read_by_id(admin_user.id)
    assert user_after_operation.coins == 0

    # Check that amount didn't change in elastic also
    get_benefits_response = await admin_client.get("/benefits/")
    assert get_benefits_response.json()[0]["amount"] == 5


@pytest.mark.asyncio
async def test_admin_get_benefit_requests_with_status_filter(
    admin_client: AsyncClient,
    benefit_requests,
):
    # Filtering on "pending"
    response = await admin_client.get(
        "/benefit-requests/", params={"status": "pending"}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()

    assert len(benefit_requests_filtered) == 2
    assert all(request["status"] == "pending" for request in benefit_requests_filtered)


@pytest.mark.asyncio
async def test_admin_get_benefit_requests_with_legal_entity_filter(
    admin_client: AsyncClient,
    legal_entity1a: LegalEntity,
    legal_entity2b: LegalEntity,
    benefit_requests,
):
    # Filtering on legal_entity1a
    response = await admin_client.get(
        "/benefit-requests/", params={"legal_entities": [legal_entity1a.id]}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert all(
        request["user"]["legal_entity"]["id"] == legal_entity1a.id
        for request in benefit_requests_filtered
    )
    assert len(benefit_requests_filtered) == 2

    # Filtering on legal_entity2b
    response = await admin_client.get(
        "/benefit-requests/", params={"legal_entities": [legal_entity2b.id]}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert all(
        request["user"]["legal_entity"]["id"] == legal_entity2b.id
        for request in benefit_requests_filtered
    )
    assert len(benefit_requests_filtered) == 2

    # Filtering on both
    response = await admin_client.get(
        "/benefit-requests/",
        params={"legal_entities": [legal_entity2b.id, legal_entity1a.id]},
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert all(
        request["user"]["legal_entity"]["id"] == legal_entity2b.id
        or request["user"]["legal_entity"]["id"] == legal_entity1a.id
        for request in benefit_requests_filtered
    )
    assert len(benefit_requests_filtered) == 4


@pytest.mark.asyncio
async def test_admin_get_benefit_requests_pagination(
    admin_client: AsyncClient,
    benefit_requests,
):
    response = await admin_client.get(
        "/benefit-requests/", params={"page": 1, "limit": 2}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_paginated = response.json()
    assert len(benefit_requests_paginated) == 2


@pytest.mark.asyncio
async def test_admin_get_benefit_requests_sorting(
    admin_client: AsyncClient,
    benefit_requests,
):
    # Descending sort on created_at
    response = await admin_client.get(
        "/benefit-requests/", params={"sort_by": "created_at", "sort_order": "desc"}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_sorted = response.json()
    # Check that the first element is BIGGER then the last one
    assert (
        benefit_requests_sorted[0]["created_at"]
        > benefit_requests_sorted[-1]["created_at"]
    )

    # Ascending sort on created_at
    response_asc = await admin_client.get(
        "/benefit-requests/", params={"sort_by": "created_at", "sort_order": "asc"}
    )
    assert response_asc.status_code == status.HTTP_200_OK
    benefit_requests_sorted_asc = response_asc.json()
    # Check that the first element is LOWER than the last one
    assert (
        benefit_requests_sorted_asc[0]["created_at"]
        < benefit_requests_sorted_asc[-1]["created_at"]
    )


@pytest.mark.asyncio
async def test_hr_get_benefit_requests_with_status_filter(
    hr_client: AsyncClient,
    benefit_requests,
):
    # Filtering on 'pending' for hr
    response = await hr_client.get("/benefit-requests/", params={"status": "pending"})
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert (
        len(benefit_requests_filtered) == 1
    )  # Only one "pending" request from user inside hr_user's legal entity
    assert all(request["status"] == "pending" for request in benefit_requests_filtered)


@pytest.mark.asyncio
async def test_hr_get_benefit_requests_with_legal_entity_filter(
    hr_client: AsyncClient,
    legal_entity1a: LegalEntity,
    legal_entity2b: LegalEntity,
    benefit_requests,
):
    # Filtering on legal_entity1a
    response = await hr_client.get(
        "/benefit-requests/", params={"legal_entities": [legal_entity1a.id]}
    )

    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert all(
        request["user"]["legal_entity"]["id"] == legal_entity1a.id
        for request in benefit_requests_filtered
    )
    assert len(benefit_requests_filtered) == 2

    # Filtering on legal_entity2b
    # Hr user has legal_entity1a so all the requests he gets should be inside it
    response = await hr_client.get(
        "/benefit-requests/", params={"legal_entities": [legal_entity2b.id]}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_filtered = response.json()
    assert all(
        request["user"]["legal_entity"]["id"] == legal_entity1a.id
        for request in benefit_requests_filtered
    )
    assert len(benefit_requests_filtered) == 2


@pytest.mark.asyncio
async def test_hr_get_benefit_requests_sorting(
    hr_client: AsyncClient,
    benefit_requests,
):
    response = await hr_client.get(
        "/benefit-requests/", params={"sort_by": "created_at", "sort_order": "desc"}
    )
    assert response.status_code == status.HTTP_200_OK
    benefit_requests_sorted = response.json()

    assert (
        benefit_requests_sorted[0]["created_at"]
        > benefit_requests_sorted[-1]["created_at"]
    )

    response_asc = await hr_client.get(
        "/benefit-requests/", params={"sort_by": "created_at", "sort_order": "asc"}
    )
    assert response_asc.status_code == status.HTTP_200_OK
    benefit_requests_sorted_asc = response_asc.json()

    assert (
        benefit_requests_sorted_asc[0]["created_at"]
        < benefit_requests_sorted_asc[-1]["created_at"]
    )


# Excel EXPORT tests


field_mappings = {
    "id": ["ID"],
    "status": ["Статус"],
    "comment": ["Комментарий"],
    "benefit_name": ["Название бенефита"],
    "user_email": ["email пользователя"],
    "user_fullname": ["ФИО пользователя"],
    "performer_email": ["email сотрудника HR"],
    "performer_fullname": ["ФИО сотрудника HR"],
    "created_at": ["Время создания"],
    "updated_at": ["Время последней модификации"],
}


async def arrange_request_export_test(client: AsyncClient, params: Optional[dict]):
    response = await client.get("/benefit-requests/export", params=params)
    assert response.status_code == status.HTTP_200_OK
    assert "Content-Disposition" in response.headers
    assert (
        "attachment; filename=benefit_requests.xlsx"
        in response.headers["Content-Disposition"]
    )
    assert (
        response.headers["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    excel_parser = ExcelParser(
        model_class=schemas.BenefitRequestReadExcel, field_mappings=field_mappings
    )
    return excel_parser.parse_excel(response.content)


@pytest.mark.excel
@pytest.mark.asyncio
async def test_export_benefit_requests_no_filters(
    admin_client: AsyncClient, benefit_requests
):
    parsed_data, errors = await arrange_request_export_test(
        client=admin_client, params=None
    )

    assert len(parsed_data) == 4
    assert all(
        isinstance(request, schemas.BenefitRequestReadExcel) for request in parsed_data
    )
    assert len(errors) == 0


@pytest.mark.excel
@pytest.mark.asyncio
async def test_export_benefit_requests_with_status_filter(
    admin_client: AsyncClient, benefit_requests
):
    parsed_data, errors = await arrange_request_export_test(
        client=admin_client, params={"status": "pending"}
    )

    assert len(parsed_data) == 2
    assert all(request.status == "pending" for request in parsed_data)
    assert len(errors) == 0


@pytest.mark.excel
@pytest.mark.asyncio
async def test_export_benefit_requests_with_legal_entity_filter(
    admin_client: AsyncClient, legal_entity1a: LegalEntity, benefit_requests
):
    parsed_data, errors = await arrange_request_export_test(
        client=admin_client, params={"legal_entity_ids": [legal_entity1a.id]}
    )

    assert len(parsed_data) == 2

    assert len(errors) == 0
