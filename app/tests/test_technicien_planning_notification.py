from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.equipement import EquipementCreate
from app.schemas.notification import NotificationCreate
from app.schemas.planning import PlanningCreate
from app.schemas.technicien import CompetenceCreate, TechnicienCreate
from app.schemas.user import UserCreate, UserRole
from app.services.equipement_service import create_equipement
from app.services.notification_service import create_notification
from app.services.planning_service import (
    create_planning,
    update_planning_dates,
    update_planning_frequence,
)
from app.services.technicien_service import (
    create_competence,
    create_technicien,
)
from app.services.user_service import create_user


def test_technicien_and_competence_flow():
    with SessionLocal() as db:
        # create user with technicien role
        uc = UserCreate(
            username="techuser",
            full_name="T",
            email="tech@example.com",
            role=UserRole.technicien,
            password="Password123!",
        )
        try:
            user = create_user(db, uc)
        except Exception:
            from app.models.user import User

            user = db.query(User).filter_by(email="tech@example.com").first()
        comp = create_competence(db, CompetenceCreate(nom="elec"))
        tc = TechnicienCreate(
            user_id=user.id,
            equipe="E1",
            disponibilite="disponible",
            competences_ids=[comp.id],
        )
        techn = create_technicien(db, tc)
        assert techn.id is not None


def test_planning_create_and_update():
    with SessionLocal() as db:
        eq = create_equipement(
            db,
            EquipementCreate(
                nom="PL-EQ", type="t", localisation="L", frequence_entretien="7"
            ),
        )
        pc = PlanningCreate(
            frequence="mensuel",
            prochaine_date=datetime.utcnow() + timedelta(days=30),
            derniere_date=None,
            equipement_id=eq.id,
        )
        planning = create_planning(db, pc)
        assert planning.id is not None
        new = update_planning_dates(
            db, planning.id, datetime.utcnow() + timedelta(days=60)
        )
        assert new.prochaine_date is not None
        updated = update_planning_frequence(db, planning.id, "journalier")
        assert updated.frequence is not None


def test_create_notification_non_email():
    with SessionLocal() as db:
        # create a user
        uc = UserCreate(
            username="noti",
            full_name="N",
            email="noti@example.com",
            role=UserRole.client,
            password="Password123!",
        )
        try:
            u = create_user(db, uc)
        except Exception:
            u = db.query(User).filter_by(email="noti@example.com").first()
        assert u is not None, "User should exist"
        # NotificationCreate requires 'type' alias and intervention_id int;
        # use intervention_id=0 for system/global
        nc = NotificationCreate(
            **{
                "type": "information",
                "canal": "sms",
                "contenu": "Hello",
                "user_id": u.id,
                "intervention_id": 0,
            }
        )
        notif = create_notification(db, nc)
        assert notif.id is not None
