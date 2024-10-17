from pathlib import Path
from typing import Any, Dict

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    TEMPLATE_FOLDER=Path(__file__).parent / "email_templates",
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
    SUPPRESS_SEND=settings.DEBUG,
)

fm = FastMail(conf)


async def send_mail(email: Dict[str, Any], subject: str, template: str):
    message = MessageSchema(
        subject=subject,
        recipients=email.get("email"),
        template_body=email.get("body"),
        subtype=MessageType.html,
    )
    await fm.send_message(message, template_name=template)
