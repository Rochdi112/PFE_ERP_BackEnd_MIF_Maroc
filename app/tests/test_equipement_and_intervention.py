from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.schemas.equipement import EquipementCreate
from app.schemas.intervention import InterventionCreate, StatutIntervention
from app.schemas.user import UserRole
from app.services.equipement_service import (
    create_equipement,
    delete_equipement,
    get_all_equipements,
)
from app.services.intervention_service import (
    create_intervention,
    get_intervention_by_id,
    update_statut_intervention,
)
from app.services.user_service import ensure_user_for_email


def create_sample_equipement(db):
    data = EquipementCreate(
        nom="EQ-1", type="machine", localisation="Site A", frequence_entretien="30"
    )
    eq = create_equipement(db, data)
    return eq


def test_equipement_crud_and_intervention_flow():
    with SessionLocal() as db:
        eq = create_sample_equipement(db)
        all_eq = get_all_equipements(db)
        assert any(e.id == eq.id for e in all_eq)

        # Prepare a user (ensure exists)
        user = ensure_user_for_email(
            db, email="resp@example.com", role=UserRole.responsable
        )

        # Create intervention against equipment
        ic = InterventionCreate(
            titre="Op1",
            description="Desc",
            type_intervention="corrective",
            statut=StatutIntervention.ouverte,
            priorite="normale",
            urgence=False,
            date_limite=(datetime.utcnow() + timedelta(days=3)),
            technicien_id=None,
            equipement_id=eq.id,
        )
        interv = create_intervention(db, ic, user_id=user.id)
        assert interv.id is not None
        fetched = get_intervention_by_id(db, interv.id)
        assert fetched.id == interv.id

        # Change statut to en_cours then cloturee
        updated = update_statut_intervention(
            db,
            interv.id,
            StatutIntervention.en_cours,
            user_id=user.id,
            remarque="start",
        )
        assert updated.statut == StatutIntervention.en_cours
        updated2 = update_statut_intervention(
            db,
            interv.id,
            StatutIntervention.cloturee,
            user_id=user.id,
            remarque="finish",
        )
        assert updated2.statut == StatutIntervention.cloturee

        # Delete equipment (should succeed because interventions exist but old logic
        # counts dynamic -> may be 0)
        try:
            delete_equipement(db, eq.id)
        except Exception:
            # acceptable if business rule prevents deletion
            pass
