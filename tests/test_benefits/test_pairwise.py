import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_benefit_pairwise_1(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 1",
        "is_active": True,
        "amount": None,
        "coins_cost": 0,
        "min_level_cost": 0,
        "adaptation_required": True,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["is_active"] == benefit_data["is_active"]
    assert data["amount"] == benefit_data["amount"]
    assert data["coins_cost"] == benefit_data["coins_cost"]
    assert data["min_level_cost"] == benefit_data["min_level_cost"]
    assert data["adaptation_required"] == benefit_data["adaptation_required"]


@pytest.mark.asyncio
async def test_create_benefit_pairwise_2(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 2",
        "is_active": True,
        "amount": 0,
        "coins_cost": 10,
        "min_level_cost": 5,
        "adaptation_required": False,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == benefit_data["amount"]


@pytest.mark.asyncio
async def test_create_benefit_pairwise_3(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 3",
        "is_active": True,
        "amount": 10,
        "coins_cost": 100,
        "min_level_cost": 10,
        "adaptation_required": True,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_create_benefit_pairwise_4(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 4",
        "is_active": False,
        "amount": None,
        "coins_cost": 10,
        "min_level_cost": 10,
        "adaptation_required": False,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_create_benefit_pairwise_5(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 5",
        "is_active": False,
        "amount": 0,
        "coins_cost": 100,
        "min_level_cost": 0,
        "adaptation_required": True,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_create_benefit_pairwise_6(async_client: AsyncClient):
    benefit_data = {
        "name": "Benefit Pairwise Test 6",
        "is_active": False,
        "amount": 10,
        "coins_cost": 0,
        "min_level_cost": 5,
        "adaptation_required": False,
    }
    response = await async_client.post("/benefits/", json=benefit_data)
    assert response.status_code == status.HTTP_201_CREATED
