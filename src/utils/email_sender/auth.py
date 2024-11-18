from fastapi import BackgroundTasks
from pydantic import EmailStr

import src.schemas.email as email_schemas
from src.config import get_settings
from src.utils.email_sender.base import send_mail
from src.utils.security import create_reset_password_token

settings = get_settings()


async def send_forget_password_email(
    email: EmailStr, background_tasks: BackgroundTasks
) -> None:
    """
    Send a password reset email to the specified email address.

    - email: The email address to which the password reset link will be sent.

    Details:
    - Generates a password reset token and includes it in a reset URL.
    - Uses the background mail sending task to send an email with a reset link.
    """
    secret_token = create_reset_password_token(email=email)

    email = email_schemas.EmailSchema.model_validate(
        {
            "email": [email],
            "body": {
                "reset_url": f"https://{settings.DOMAIN}/reset-password?token={secret_token}",  # noqa: E231
            },
        }
    )

    background_tasks.add_task(
        send_mail,
        email.model_dump(),
        f"Смена пароля на сайте {settings.APP_TITLE}",
        "reset-password.html",
    )
