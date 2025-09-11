from app.schemas.notification import NotificationCreate
from app.schemas.user import UserCreate, UserRole
from app.services.notification_service import create_notification
from app.services.user_service import create_user


def test_create_notification_non_email(db_session):
    u = create_user(
        db_session,
        UserCreate(
            username="n1",
            full_name="N",
            email="n1@example.com",
            role=UserRole.client,
            password="Password123!",
        ),
    )
    nc = NotificationCreate(
        **{
            "type": "information",
            "canal": "sms",
            "contenu": "hi",
            "user_id": u.id,
            "intervention_id": 0,
        }
    )
    notif = create_notification(db_session, nc)
    assert notif.id is not None
