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
    assert response.status_code == status.HTTP_404_NOT_FOUND


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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_benefit_request_valid(async_client: AsyncClient):
    request_id = 1
    update_data = {"comment": "Some test comment"}
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


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_1(async_client: AsyncClient):
    """
    Test 1:
    - benefit_id_validity: Valid
    - user_id_validity: Valid
    - user_has_enough_coins: Yes
    - user_meets_level_requirement: Yes
    - benefit_amount_sufficient: Yes
    - adaptation_match: Yes
    Expected: Success
    """
    benefit_data = {
        "name": "Benefit Test 1",
        "coins_cost": 10,
        "min_level_cost": 1,
        "amount": 10,
        "adaptation_required": True,
    }
    benefit_response = await async_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    user_data = {
        "email": "user_test1@example.com",
        "firstname": "User",
        "lastname": "Test1",
        "role": "employee",
        "coins": 10,
        "hired_at": "2023-01-01",
        "is_adapted": True,
    }
    user_response = await async_client.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_2(async_client: AsyncClient):
    """
    Test 2:
    - benefit_id_validity: Valid
    - user_id_validity: Valid
    - user_has_enough_coins: No
    - user_meets_level_requirement: No
    - benefit_amount_sufficient: No
    - adaptation_match: No
    Expected: Failure due to multiple reasons
    """
    benefit_data = {
        "name": "Benefit Test 2",
        "coins_cost": 10,
        "min_level_cost": 5,
        "amount": 0,
        "adaptation_required": False,
    }
    benefit_response = await async_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    user_data = {
        "email": "user_test2@example.com",
        "firstname": "User",
        "lastname": "Test2",
        "role": "employee",
        "coins": 5,
        "hired_at": "2023-10-01",
        "is_adapted": True,
    }
    user_response = await async_client.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_3(async_client: AsyncClient):
    """
    Test 3:
    - benefit_id_validity: Valid
    - user_id_validity: Invalid
    - user_has_enough_coins: Yes
    - user_meets_level_requirement: No
    - benefit_amount_sufficient: Yes
    - adaptation_match: No
    Expected: Failure due to invalid user_id
    """
    benefit_data = {
        "name": "Benefit Test 3",
        "coins_cost": 10,
        "min_level_cost": 5,
        "amount": 10,
        "adaptation_required": False,
    }
    benefit_response = await async_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    user_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_4(async_client: AsyncClient):
    """
    Test 4:
    - benefit_id_validity: Valid
    - user_id_validity: Invalid
    - user_has_enough_coins: No
    - user_meets_level_requirement: Yes
    - benefit_amount_sufficient: No
    - adaptation_match: Yes
    Expected: Failure due to invalid user_id
    """
    benefit_data = {
        "name": "Benefit Test 4",
        "coins_cost": 15,
        "min_level_cost": 1,
        "amount": 0,
        "adaptation_required": True,
    }
    benefit_response = await async_client.post("/benefits/", json=benefit_data)
    assert benefit_response.status_code == status.HTTP_201_CREATED
    benefit_id = benefit_response.json()["id"]

    user_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_5(async_client: AsyncClient):
    """
    Test 5:
    - benefit_id_validity: Invalid
    - user_id_validity: Valid
    - user_has_enough_coins: Yes
    - user_meets_level_requirement: No
    - benefit_amount_sufficient: No
    - adaptation_match: Yes
    Expected: Failure due to invalid benefit_id
    """
    user_data = {
        "email": "user_test5@example.com",
        "firstname": "User",
        "lastname": "Test5",
        "role": "employee",
        "coins": 20,
        "hired_at": "2023-10-01",
        "is_adapted": True,
    }
    user_response = await async_client.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    benefit_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_6(async_client: AsyncClient):
    """
    Test 6:
    - benefit_id_validity: Invalid
    - user_id_validity: Valid
    - user_has_enough_coins: No
    - user_meets_level_requirement: Yes
    - benefit_amount_sufficient: Yes
    - adaptation_match: No
    Expected: Failure due to invalid benefit_id
    """
    user_data = {
        "email": "user_test6@example.com",
        "firstname": "User",
        "lastname": "Test6",
        "role": "employee",
        "coins": 5,
        "hired_at": "2020-01-01",
        "is_adapted": False,
    }
    user_response = await async_client.post("/users/", json=user_data)
    assert user_response.status_code == status.HTTP_201_CREATED
    user_id = user_response.json()["id"]

    benefit_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_7(async_client: AsyncClient):
    """
    Test 7:
    - benefit_id_validity: Invalid
    - user_id_validity: Invalid
    - user_has_enough_coins: Yes
    - user_meets_level_requirement: Yes
    - benefit_amount_sufficient: No
    - adaptation_match: No
    Expected: Failure due to invalid benefit_id and user_id
    """
    benefit_id = 9999
    user_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_request_pairwise_8(async_client: AsyncClient):
    """
    Test 8:
    - benefit_id_validity: Invalid
    - user_id_validity: Invalid
    - user_has_enough_coins: No
    - user_meets_level_requirement: No
    - benefit_amount_sufficient: Yes
    - adaptation_match: Yes
    Expected: Failure due to invalid benefit_id and user_id
    """
    benefit_id = 9999
    user_id = 9999

    request_data = {
        "benefit_id": benefit_id,
        "user_id": user_id,
    }
    response = await async_client.post("/benefit-requests/", json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
