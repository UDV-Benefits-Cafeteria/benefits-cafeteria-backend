# tests/test_ping.py
from httpx import AsyncClient


async def test_ping(async_client: AsyncClient):
    response = await async_client.get("/api/v1/ping")
    assert response.json() == {"success": True}
