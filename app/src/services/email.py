from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.src.config.config import settings
import logging
from pathlib import Path
from datetime import datetime, timedelta
import jwt
from typing import Optional
from functools import lru_cache
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

def create_verification_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "email_verification"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

async def send_email(email_to: str, subject: str, template_name: str, template_vars: dict) -> bool:
    try:
        if not settings.mail_test_mode:
            try:
                valid = validate_email(email_to)
                email_to = valid.email
            except EmailNotValidError as e:
                logger.error(f"Invalid email: {str(e)}")
                return False

        if settings.mail_test_mode:
            email_to = settings.mail_test_recipient
            logger.info(f"Test mode active. Redirecting email to {email_to}")

        html_content = load_template(template_name)
        for key, value in template_vars.items():
            html_content = html_content.replace(f"{{{{ {key} }}}}", str(value))

        msg = MIMEMultipart()
        msg["From"] = settings.mail_from
        msg["To"] = email_to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        async with SMTP(
            hostname=settings.mail_server,
            port=settings.mail_port,
            username=settings.mail_username,
            password=settings.mail_password,
            start_tls=settings.mail_starttls,
            timeout=10
        ) as server:
            await server.send_message(msg)
        logger.info(f"Email successfully sent to {email_to}")
        return True
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}", exc_info=True)
        return False
    
async def send_verification_email(email: str, user_id: int) -> bool:
    token = create_verification_token(user_id)
    return await send_email(
        email_to=email,
        subject="Підтвердження email у системі GOIT",
        template_name="verification_email.html",
        template_vars={"verification_link": f"http://localhost:8000/auth/verify-email?token={token}", "support_email": "support@goit.com"}
    )

async def send_password_reset_email(email: str, reset_token: str) -> bool:
    return await send_email(
        email_to=email,
        subject="Відновлення паролю GOIT",
        template_name="reset_password.html",
        template_vars={"reset_link": f"{settings.frontend_url}/reset-password?token={reset_token}", "expiration_hours": "24", "support_email": settings.mail_from}
    )

def create_password_reset_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "password_reset"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

@lru_cache(maxsize=32)
def load_template(template_name: str) -> str:
    template_path = Path(__file__).parent / "templates" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()