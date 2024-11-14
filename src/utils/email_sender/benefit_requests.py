from fastapi import BackgroundTasks
from pydantic import EmailStr

import src.schemas.email as email_schemas
from src.config import get_settings
from src.utils.email_sender.base import send_mail

settings = get_settings()


async def send_users_benefit_request_created_email(
    email: EmailStr,
    firstname: str,
    benefit_id: int,
    benefit_name: str,
    benefit_price: int,
    benefit_image_url: str,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Send a benefit request created email to the specified email address.

    - email: The email address to which the benefit request created email will be sent.
    """

    email = email_schemas.EmailSchema.model_validate(
        {
            "email": [email],
            "body": {
                "product": settings.APP_TITLE,
                "name": firstname,
                "benefit_image": (benefit_image_url),
                "benefit_name": benefit_name,
                "benefit_price": benefit_price,
                "benefit_url": f"https://{settings.DOMAIN}/main/benefits/{benefit_id}",  # noqa: E231
                "requests_url": f"https://{settings.DOMAIN}/main/history",  # noqa: E231
            },
        }
    )

    background_tasks.add_task(
        send_mail,
        email.model_dump(),
        f"Запрос на бенефит на {settings.APP_TITLE}",  # noqa: Typo
        "benefit-request.html",
    )


async def send_users_benefit_request_updated_email(
    email: EmailStr,
    firstname: str,
    new_status: str,
    benefit_id: int,
    benefit_name: str,
    benefit_price: int,
    benefit_image_url: str,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Send a benefit request created email to the specified email address.

    - email: The email address to which the benefit request created email will be sent.
    """

    email = email_schemas.EmailSchema.model_validate(
        {
            "email": [email],
            "body": {
                "request_status": new_status,
                "name": firstname,
                "benefit_image": benefit_image_url,
                "benefit_name": benefit_name,
                "benefit_price": benefit_price,
                "benefit_url": f"https://{settings.DOMAIN}/main/benefits/{benefit_id}",
                "requests_url": f"https://{settings.DOMAIN}/main/history",
            },
        }
    )

    background_tasks.add_task(
        send_mail,
        email.model_dump(),
        f"Смена статуса у запроса на {settings.APP_TITLE}",  # noqa: Typo
        "benefit-response.html",
    )
