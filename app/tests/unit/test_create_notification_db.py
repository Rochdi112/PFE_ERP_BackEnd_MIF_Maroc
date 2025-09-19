from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db import database
from app.models.intervention import Intervention, InterventionType
from app.models.notification import CanalNotification, Notification
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCreate
from app.services.notification_service import create_notification


def setup_inmemory_db(monkeypatch):
    # Force sqlite engine
    monkeypatch.setitem(__import__("sys").modules, "pytest", object())
    eng = database._create_default_engine()
    monkeypatch.setattr(database, "engine", eng)
    # Create schema
    database.Base.metadata.create_all(bind=eng)
    return eng


def test_create_notification_non_email(monkeypatch):
    setup_inmemory_db(monkeypatch)
    SessionLocal = database.SessionLocal
    db: Session = SessionLocal()

    # create user
    u = User(
        username="u1", email="u1@example.com", hashed_password=get_password_hash("Password123!"), role=UserRole.client
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    # create intervention minimal
    it = Intervention(titre="t", type_intervention=InterventionType.corrective)
    db.add(it)
    db.commit()
    db.refresh(it)

    # Build NotificationCreate
    nc = NotificationCreate(
        type="information",
        canal="log",
        contenu="test",
        intervention_id=it.id,
        user_id=u.id,
    )

    notif = create_notification(db, nc)
    assert isinstance(notif, Notification)
    # Check persisted
    q = db.query(Notification).filter(Notification.id == notif.id).first()
    assert q is not None
    assert q.user_id == u.id
    assert q.canal == CanalNotification.log
    db.close()
