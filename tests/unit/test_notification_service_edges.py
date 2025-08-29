import pytest

from app.services.notification_service import create_notification, send_email_notification
from app.schemas.notification import NotificationCreate


def test_create_notification_missing_user(db_session):
    # NotificationCreate requires 'type' alias and integer intervention_id; use 0 for non-existent
    nc = NotificationCreate(**{"type": "information", "canal": "email", "contenu": "t", "user_id": 9999, "intervention_id": 0})
    with pytest.raises(Exception):
        create_notification(db_session, nc)


def test_send_email_template_not_found():
    # craft a dummy notification object with a non-existing type to trigger TemplateNotFound
    class Dummy:
        type_notification = type("T", (), {"value": "nonexistent"})()
        canal = "email"
        contenu = "c"

    with pytest.raises(Exception):
        send_email_notification("noone@example.com", Dummy())
