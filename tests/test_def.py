from httpx import AsyncClient


def testing():
    assert 1 == 1
    assert 2 == 2


async def test2(async_client: AsyncClient):
    assert async_client is not None
