from app.schemas.technicien import CompetenceCreate, TechnicienCreate
from app.schemas.user import UserCreate, UserRole
from app.services.technicien_service import create_competence, create_technicien
from app.services.user_service import create_user


def test_create_competence_and_technicien_flow(db_session):
    comp = create_competence(db_session, CompetenceCreate(nom="compx"))
    u = create_user(
        db_session,
        UserCreate(
            username="tuser",
            full_name="T",
            email="tuser@example.com",
            role=UserRole.technicien,
            password="Password123!",
        ),
    )
    tc = TechnicienCreate(
        user_id=u.id, equipe="E", disponibilite="disponible", competences_ids=[comp.id]
    )
    tech = create_technicien(db_session, tc)
    assert tech.id is not None
