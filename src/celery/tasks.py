import asyncio

from celery import shared_task
from src.utils.email import send_mail


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    name="email:email_send",
)
def background_send_mail(self, email, subject, template) -> str:
    result = asyncio.run(send_mail(email, subject, template))
    return result
