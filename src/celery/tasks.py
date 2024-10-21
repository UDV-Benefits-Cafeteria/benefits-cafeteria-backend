import asyncio
from typing import Any

from celery import shared_task
from src.services.sessions import SessionsService
from src.utils.email import send_mail


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    name="email:email_send",
)
def background_send_mail(
    self, email: dict[str, Any], subject: str, template: str
) -> None:
    result = asyncio.run(send_mail(email, subject, template))
    return result


@shared_task(
    name="sessions:cleanup_expired_sessions",
)
def cleanup_expired_sessions_task(self):
    async def run_cleanup():
        service = SessionsService()
        deleted_count = await service.cleanup_expired_sessions()
        return deleted_count

    return asyncio.run(run_cleanup())
