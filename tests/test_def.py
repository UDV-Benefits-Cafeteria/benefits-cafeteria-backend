from httpx import AsyncClient


def testing():
    assert 1 == 1
    assert 2 == 2


async def test2(ac: AsyncClient):
    assert ac is not None
