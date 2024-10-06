import asyncio

from celery import shared_task


async def async_test_task():
    await asyncio.sleep(3)
    return "Пупупуу"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="tests:tests_task",
)
def test_task(self) -> str:
    result = asyncio.run(async_test_task())
    return result
