from fastapi import BackgroundTasks
from pydantic import EmailStr

import src.schemas.email as email_schemas
from src.config import get_settings
from src.utils.email_sender.base import send_mail

settings = get_settings()


async def send_user_greeting_email(
    email: EmailStr, firstname: str, background_tasks: BackgroundTasks
) -> None:
    """
    Send a greeting email to the specified email address.

    - email: The email address to which the greeting will be sent.
    """

    email = email_schemas.EmailSchema.model_validate(
        {
            "email": [email],
            "body": {
                "name": firstname,
                "product": settings.APP_TITLE,
                "register_url": f"https://{settings.DOMAIN}/register?email={email}",  # noqa: E231
            },
        }
    )

    background_tasks.add_task(
        send_mail,
        email.model_dump(),
        f"Добро пожаловать на {settings.APP_TITLE}",  # noqa: Typo
        "register.html",
    )


async def send_user_coin_update_email(
    email: EmailStr,
    firstname: str,
    added_coins_amount: int,
    current_coins_balance: int,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Send a coin update email to the specified email address.

    - email: The email address to which the coin update will be sent.
    """

    email = email_schemas.EmailSchema.model_validate(
        {
            "email": [email],
            "body": {
                "operation_type": "increase" if added_coins_amount > 0 else "decrease",
                "name": firstname,
                "amount_change": added_coins_amount,
                "current_balance": current_coins_balance,
                "home_url": f"https://{settings.DOMAIN}/main/account",  # noqa: E231
            },
        }
    )

    background_tasks.add_task(
        send_mail,
        email.model_dump(),
        f"{'Пополнение' if added_coins_amount > 0 else 'Списание'} с баланса на {settings.APP_TITLE}",  # noqa: Typo
        "balance-changes.html",
    )
