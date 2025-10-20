import resend
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr
from app.core.config import settings

# Initialize Resend with your API key
resend.api_key = settings.RESEND_API_KEY

# Template folder path
TEMPLATE_FOLDER = Path(settings.TEMPLATE_FOLDER)

# Initialize Jinja2 environment for template rendering
template_env = Environment(loader=FileSystemLoader(str(TEMPLATE_FOLDER)))


async def send_notification_email(email_to: EmailStr, subject: str, body: dict):
    """
    Send email using Resend API with HTML template
    
    Args:
        email_to: Recipient email address
        subject: Email subject line
        body: Dictionary containing template variables (e.g., {"title": "...", "name": "..."})
    """
    try:
        # Load and render the HTML template
        template = template_env.get_template("email.html")
        html_content = template.render(**body)
        
        # Prepare email parameters
        params = {
            "from": f"{settings.MAIL_FROM_NAME} <noreply@fplpadi.site>",
            "to": [email_to],
            "subject": subject,
            "html": html_content,
        }
        
        # Send email via Resend
        email = resend.Emails.send(params)
        
        return email
        
    except Exception as e:
        # Re-raise the exception so it can be caught in the endpoint
        raise Exception(f"Failed to send email: {str(e)}")