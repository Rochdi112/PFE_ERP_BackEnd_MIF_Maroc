import pytest
from unittest.mock import patch


def test_send_email_template_not_found(db_session):
    from app.services.notification_service import send_email_notification
    from app.models.notification import Notification, TypeNotification

    class N:
        type_notification = TypeNotification.information
        contenu = "test"

    # Point to a non-existing template by using a made-up type
    n = Notification()
    n.type_notification = TypeNotification.information
    n.contenu = "hello"

    # monkeypatch the env to raise TemplateNotFound
    from jinja2 import TemplateNotFound
    from app.services import notification_service as ns

    original_env = ns.env
    try:
        class DummyEnv:
            def get_template(self, name):
                raise TemplateNotFound(name)

        ns.env = DummyEnv()
        with pytest.raises(Exception):
            send_email_notification("u@example.com", n)
    finally:
        ns.env = original_env


def test_send_email_smtp_failure(db_session, monkeypatch):
    from app.services.notification_service import send_email_notification
    from app.models.notification import Notification, TypeNotification

    n = Notification()
    n.type_notification = TypeNotification.information
    n.contenu = "hello"

    class FakeSMTP:
        def __init__(self, *a, **k):
            pass
        def starttls(self):
            pass
        def login(self, u, p):
            pass
        def sendmail(self, a, b, c):
            raise RuntimeError("SMTP broken")
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)
    with pytest.raises(Exception):
        send_email_notification("u@example.com", n)
