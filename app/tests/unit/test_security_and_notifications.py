from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core import security


def test_password_hash_and_verify():
    pw = "Secret123!"
    h = security.get_password_hash(pw)
    assert isinstance(h, str) and h != pw
    assert security.verify_password(pw, h)


def test_password_policy_enforces_complexity():
    with pytest.raises(HTTPException):
        security.validate_password_policy("weakpass")

    # Should not raise
    security.validate_password_policy("Complexe123!")


def test_create_and_verify_token_roundtrip():
    data = {"sub": "1", "email": "a@b.com"}
    token = security.create_access_token(
        data.copy(), expires_delta=timedelta(minutes=1)
    )
    payload = security.verify_token(token)
    assert payload.get("sub") == "1"
    assert payload.get("email") == "a@b.com"


def test_verify_token_invalid():
    with pytest.raises(HTTPException):
        security.verify_token("invalid.token")


def test_send_email_template_not_found():
    # Test that HTTPException is raised when template is not found
    from jinja2 import TemplateNotFound

    from app.services.notification_service import send_email_notification

    mock_env_instance = MagicMock()
    mock_env_instance.get_template.side_effect = TemplateNotFound("missing")

    # Create a dummy notification-like object
    class DummyType:
        value = "information"

    dummy = MagicMock()
    dummy.type_notification = DummyType()
    dummy.contenu = "Contenu test"

    # Expect HTTPException because template missing
    with pytest.raises(HTTPException):
        send_email_notification("to@example.com", dummy, env_param=mock_env_instance)


def test_send_email_smtp_failure():
    # Test that HTTPException is raised when SMTP fails
    from app.services.notification_service import send_email_notification

    mock_env_instance = MagicMock()
    tmpl = MagicMock()
    tmpl.render.return_value = "<p>ok</p>"
    mock_env_instance.get_template.return_value = tmpl

    # Create a dummy notification-like object
    class DummyType:
        value = "information"

    dummy = MagicMock()
    dummy.type_notification = DummyType()
    dummy.contenu = "Contenu test"

    # Mock SMTP to raise exception
    with patch("app.services.notification_service.smtplib") as mock_smtplib:
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.starttls.return_value = None
        mock_smtp_instance.login.return_value = None
        mock_smtp_instance.sendmail.side_effect = Exception("smtp fail")
        mock_smtp_instance.quit.return_value = None
        mock_smtplib.SMTP.return_value = mock_smtp_instance

        with pytest.raises(HTTPException):
            send_email_notification(
                "to@example.com", dummy, env_param=mock_env_instance
            )