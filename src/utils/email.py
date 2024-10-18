from pathlib import Path
from typing import Any

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
    SUPPRESS_SEND=int(settings.DEBUG),
)

fm = FastMail(conf)


async def send_mail(email: dict[str, Any], subject: str, template: str):
    """
    Asynchronously sends an email using the provided email schema, subject, and template.

    :param email: An instance of EmailSchema containing the recipient's email address and the email body.
    :type email: schemas.EmailSchema
    :param subject: The subject line of the email.
    :type subject: str
    :param template: The name of the HTML template to use for the email content.
    :type template: str

    :return: None. The function sends an email and does not return a value.
    :rtype: None
    """
    message = MessageSchema(
        subject=subject,
        recipients=email.get("email"),
        template_body=email.get("body"),
        subtype=MessageType.html,
    )
    await fm.send_message(message, template_name=template)
