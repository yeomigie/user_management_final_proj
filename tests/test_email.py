import pytest
from app.services.email_service import EmailService

@pytest.mark.asyncio
async def test_send_markdown_email(email_service, monkeypatch):
    # spy storage
    sent = []
    # replace send_email so it just records its arguments
    monkeypatch.setattr(
        email_service.smtp_client,
        "send_email",
        lambda to_addr, subject, body: sent.append((to_addr, subject, body))
    )

    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "verification_url": "http://example.com/verify?token=abc123"
    }
    await email_service.send_user_email(user_data, "email_verification")

    # verify exactly one email went out
    assert len(sent) == 1

    to_addr, subject, body = sent[0]
    assert to_addr == user_data["email"]
    assert "Verify Your Email Address" in subject
    assert user_data["verification_url"] in body
    assert user_data["name"] in body

@pytest.mark.asyncio
async def test_send_promotion_email(email_service, monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_service.smtp_client,
        "send_email",
        lambda to_addr, subject, body: sent.append((to_addr, subject, body))
    )

    test_email = "test@example.com"
    await email_service.send_pro_promotion_email(test_email)

    assert len(sent) == 1
    to_addr, subject, body = sent[0]
    assert to_addr == test_email
    assert "Congratulations on Your Professional Upgrade" in subject
    assert "Professional Membership" in body