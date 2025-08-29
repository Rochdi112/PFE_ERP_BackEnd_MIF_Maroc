import pytest
from app.db.database import SessionLocal
from app.services.intervention_service import create_intervention, update_statut_intervention
from app.schemas.intervention import InterventionCreate, StatutIntervention
from app.services.equipement_service import create_equipement
from app.schemas.equipement import EquipementCreate
from app.services.user_service import ensure_user_for_email
from app.schemas.user import UserRole
from fastapi import HTTPException
from datetime import datetime


def test_update_statut_invalid_transitions():
    with SessionLocal() as db:
        eq = create_equipement(db, EquipementCreate(nom="IEQ", type="t", localisation="L", frequence_entretien="7"))
        user = ensure_user_for_email(db, email="ie@example.com", role=UserRole.responsable)
        ic = InterventionCreate(titre="t", description="d", type_intervention="corrective", statut=StatutIntervention.ouverte, priorite="normale", urgence=False, date_limite=None, technicien_id=None, equipement_id=eq.id)
        interv = create_intervention(db, ic, user_id=user.id)
        # attempt invalid archive transition directly
        with pytest.raises(HTTPException):
            update_statut_intervention(db, interv.id, StatutIntervention.archivee, user_id=user.id, remarque="bad")
