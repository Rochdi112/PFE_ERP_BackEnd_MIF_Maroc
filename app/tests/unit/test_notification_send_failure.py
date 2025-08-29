import pytest
from app.services.notification_service import send_email_notification
from app.models.notification import Notification
from app.core.config import settings
from app.models.user import User


def test_send_email_template_missing_raises(monkeypatch):
    # prepare dummy notification and user
    notif = Notification(type_notification=object(), canal="email", contenu="x", user_id=1, intervention_id=None)
    # monkeypatch jinja env to raise
    class DummyEnv:
        def get_template(self, name):
            raise Exception("not found")

    from app.services import notification_service as ns
    monkeypatch.setattr(ns, 'env', DummyEnv())
    with pytest.raises(Exception):
        send_email_notification("a@b.com", notif)
