from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from pydantic import EmailStr

#Email config requirements
MAIL_USERNAME=settings.MAIL_USERNAME
MAIL_PASSWORD=settings.MAIL_PASSWORD
MAIL_FROM=settings.MAIL_FROM
MAIL_PORT=settings.MAIL_PORT
MAIL_SERVER=settings.MAIL_SERVER
MAIL_FROM_NAME=settings.MAIL_FROM_NAME
TEMPLATE_FOLDER=settings.TEMPLATE_FOLDER

conf = ConnectionConfig(
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    MAIL_DEBUG=0,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=0,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
)


async def send_notification_email(email_to: EmailStr, subject:str, body:dict):
    fm = FastMail(conf)
    message = MessageSchema(
        recipients= [email_to],
        subject= subject,
        template_body=body,
        subtype="html"
    )

    await fm.send_message(message=message, template_name="email.html")
