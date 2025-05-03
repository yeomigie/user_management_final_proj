import pytest
from app.services.email_service import EmailService
from app.utils.template_manager import TemplateManager

@pytest.mark.asyncio
async def test_send_markdown_email(email_service):
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "verification_url": "http://example.com/verify?token=abc123"
    }
    # send_user_email is a stub—no real SMTP call
    await email_service.send_user_email(user_data, 'email_verification')

@pytest.mark.asyncio
async def test_send_promotion_email(email_service):
    test_email = "test@example.com"
    # send_pro_promotion_email is a stub—no real SMTP call
    await email_service.send_pro_promotion_email(test_email)
