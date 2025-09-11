from app.models.user import User
from app.schemas.equipement import EquipementCreate
from app.schemas.user import UserCreate, UserRole
from app.services.equipement_service import create_equipement
from app.services.user_service import create_user


def create_admin(db):
    try:
        return create_user(
            db,
            UserCreate(
                username="adminf",
                full_name="Admin F",
                email="adminf@example.com",
                role=UserRole.admin,
                password="adminpass123!",
            ),
        )
    except Exception:
        # fallback: query existing
        return db.query(User).filter_by(email="adminf@example.com").first()


def create_equipement_helper(db, name="EQ-FACT"):
    return create_equipement(
        db,
        EquipementCreate(
            nom=name, type="machine", localisation="Loc", frequence_entretien="30"
        ),
    )
