import pytest
from fastapi import status
from httpx import AsyncClient

from src.schemas.benefit import BenefitRead
from src.schemas.user import UserRead
from src.services.benefits import BenefitsService


@pytest.mark.asyncio
async def test_get_benefit_invalid(admin_client: AsyncClient):
    response = await admin_client.get("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "coins_cost, expected_status",
    [
        (-1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (0, status.HTTP_201_CREATED),
        (1, status.HTTP_201_CREATED),
        (9999999, status.HTTP_201_CREATED),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_coins_cost_boundary(
    admin_client: AsyncClient, coins_cost, expected_status
):
    benefit_data = {
        "name": f"Benefit Coins Cost {coins_cost}",
        "coins_cost": coins_cost,
        "min_level_cost": 0,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "amount, expected_status",
    [
        (-1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (0, status.HTTP_201_CREATED),
        (1, status.HTTP_201_CREATED),
        (None, status.HTTP_201_CREATED),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_amount_boundary(
    admin_client: AsyncClient, amount, expected_status
):
    benefit_data = {
        "name": f"Benefit Amount {amount}",
        "coins_cost": 10,
        "min_level_cost": 0,
        "amount": amount,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "name, expected_status",
    [
        ("", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("A", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("AA", status.HTTP_201_CREATED),
        ("Valid Benefit Name", status.HTTP_201_CREATED),
        ("A" * 100, status.HTTP_201_CREATED),
        ("A" * 101, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_name_length(
    admin_client: AsyncClient, name, expected_status
):
    benefit_data = {
        "name": name,
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "real_currency_cost, expected_status",
    [
        (-0.01, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (0.00, status.HTTP_201_CREATED),
        (0.01, status.HTTP_201_CREATED),
        (99999999.99, status.HTTP_201_CREATED),
        (100000000.00, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_create_benefit_real_currency_cost_boundary(
    admin_client: AsyncClient, real_currency_cost, expected_status
):
    benefit_data = {
        "name": f"Benefit Real Currency Cost {real_currency_cost}",
        "coins_cost": 10,
        "min_level_cost": 0,
        "real_currency_cost": real_currency_cost,
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_update_benefit(admin_client: AsyncClient, category, admin_user):
    benefit_data = {
        "name": "Original Benefit",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    create_response = await admin_client.post("/benefits/", json=benefit_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    benefit = create_response.json()

    update_data = {
        "name": "Updated Benefit",
        "coins_cost": 20,
        "category_id": category.id,
    }
    update_response = await admin_client.patch(
        f"/benefits/{benefit['id']}", json=update_data
    )
    assert update_response.status_code == status.HTTP_200_OK
    updated_benefit = update_response.json()
    assert updated_benefit["name"] == update_data["name"]
    assert updated_benefit["coins_cost"] == update_data["coins_cost"]
    assert updated_benefit["category"]["id"] == update_data["category_id"]

    admin: UserRead = UserRead.model_validate(admin_user)

    benefit_in_db: BenefitRead = await BenefitsService().read_by_id(
        entity_id=benefit["id"], current_user=admin
    )

    assert benefit_in_db is not None

    assert benefit_in_db.model_dump() == updated_benefit


@pytest.mark.asyncio
async def test_update_benefit_invalid(admin_client: AsyncClient):
    update_data = {
        "name": "Updated Benefit",
        "coins_cost": 20,
    }
    response = await admin_client.patch("/benefits/9999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit(admin_client: AsyncClient):
    benefit_data = {
        "name": "Benefit to Delete",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    create_response = await admin_client.post("/benefits/", json=benefit_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    benefit = create_response.json()

    delete_response = await admin_client.delete(f"/benefits/{benefit['id']}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await admin_client.get(f"/benefits/{benefit['id']}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_benefit_invalid(admin_client: AsyncClient):
    response = await admin_client.delete("/benefits/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_benefit_with_unknown_fields(admin_client: AsyncClient):
    benefit_data = {
        "name": "Benefit with Unknown Fields",
        "coins_cost": 10,
        "min_level_cost": 0,
        "unknown_field": "some value",
    }
    response = await admin_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
    benefit = response.json()
    assert "unknown_field" not in benefit


@pytest.mark.asyncio
async def test_employee_cannot_create_benefit(employee_client: AsyncClient):
    benefit_data = {
        "name": "Employee Attempted Benefit",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    response = await employee_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_hr_create_benefit(hr_client: AsyncClient):
    benefit_data = {
        "name": "HR Created Benefit",
        "coins_cost": 10,
        "min_level_cost": 0,
    }
    response = await hr_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize("num_benefits", [1, 2, 4])
@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_benefit_creation(
    hr_client: AsyncClient,
    num_benefits,
    setup_indices,
):
    for i in range(num_benefits):
        benefit_data = {
            "name": f"Benefit{i}",
            "coins_cost": i,
            "min_level_cost": i,
        }
        response = await hr_client.post("/benefits/", json=benefit_data)
        assert response.status_code == status.HTTP_201_CREATED

        benefit_in_db = await BenefitsService().read_by_id(response.json()["id"])
        assert benefit_in_db is not None

    get_response = await hr_client.get("/benefits/")
    assert len(get_response.json()) == num_benefits


@pytest.mark.elastic
@pytest.mark.asyncio
async def test_elastic_benefit_deletion(
    hr_client: AsyncClient,
    setup_indices,
):
    benefit_data = {
        "name": "BenefitDelete",
        "coins_cost": 123,
        "min_level_cost": 123,
    }
    response = await hr_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED

    benefit_in_db: BenefitRead = await BenefitsService().read_by_id(
        response.json()["id"]
    )
    assert benefit_in_db is not None

    get_response = await hr_client.get("/benefits/")
    assert get_response.status_code == status.HTTP_200_OK

    delete_response = await hr_client.delete(f"/benefits/{benefit_in_db.id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["is_success"] is True

    get_response = await hr_client.get("/benefits/")
    assert get_response.status_code == status.HTTP_200_OK

    assert get_response.json() == []
