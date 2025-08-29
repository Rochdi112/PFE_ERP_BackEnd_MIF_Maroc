import pytest
from app.core import security
from datetime import timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


def test_password_hash_and_verify():
    pw = 'secret123'
    h = security.get_password_hash(pw)
    assert isinstance(h, str) and h != pw
    assert security.verify_password(pw, h)


def test_create_and_verify_token_roundtrip():
    data = {'sub': '1', 'email': 'a@b.com'}
    token = security.create_access_token(data.copy(), expires_delta=timedelta(minutes=1))
    payload = security.verify_token(token)
    assert payload.get('sub') == '1'
    assert payload.get('email') == 'a@b.com'


def test_verify_token_invalid():
    with pytest.raises(HTTPException):
        security.verify_token('invalid.token')


@patch('app.services.notification_service.env')
@patch('smtplib.SMTP')
def test_send_email_template_not_found_and_smtp(mock_smtp, mock_env):
    # Configure env.get_template to raise TemplateNotFound
    from jinja2 import TemplateNotFound
    mock_env.get_template.side_effect = TemplateNotFound('missing')

    # Create a dummy notification-like object
    class DummyType:
        value = 'information'

    dummy = MagicMock()
    dummy.type_notification = DummyType()
    dummy.contenu = 'Contenu test'

    # Expect HTTPException because template missing
    from app.services.notification_service import send_email_notification
    with pytest.raises(HTTPException):
        send_email_notification('to@example.com', dummy)

    # Now simulate template present but SMTP raises to ensure exception handling
    mock_env.get_template.side_effect = None
    tmpl = MagicMock()
    tmpl.render.return_value = '<p>ok</p>'
    mock_env.get_template.return_value = tmpl

    # Configure SMTP to raise on send
    instance = mock_smtp.return_value.__enter__.return_value
    instance.starttls.return_value = None
    instance.login.return_value = None
    instance.sendmail.side_effect = Exception('smtp fail')

    with pytest.raises(HTTPException):
        send_email_notification('to@example.com', dummy)
