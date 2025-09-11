import pytest

from app.schemas.equipement import EquipementCreate
from app.schemas.intervention import InterventionCreate, StatutIntervention
from app.schemas.user import UserRole
from app.services.equipement_service import create_equipement
from app.services.intervention_service import (
    create_intervention,
    update_statut_intervention,
)
from app.services.user_service import ensure_user_for_email


def test_create_intervention_missing_equipement_raises(db_session):
    ic = InterventionCreate(
        titre="t",
        description="d",
        type_intervention="corrective",
        statut=StatutIntervention.ouverte,
        priorite="normale",
        urgence=False,
        date_limite=None,
        technicien_id=None,
        equipement_id=999999,
    )
    with pytest.raises(Exception):
        create_intervention(db_session, ic, user_id=1)


def test_update_statut_invalid_archive_transition(db_session):
    eq = create_equipement(
        db_session,
        EquipementCreate(
            nom="IEQ2", type="t", localisation="L", frequence_entretien="7"
        ),
    )
    user = ensure_user_for_email(
        db_session, email="u2@example.com", role=UserRole.responsable
    )
    ic = InterventionCreate(
        titre="t",
        description="d",
        type_intervention="corrective",
        statut=StatutIntervention.ouverte,
        priorite="normale",
        urgence=False,
        date_limite=None,
        technicien_id=None,
        equipement_id=eq.id,
    )
    interv = create_intervention(db_session, ic, user_id=user.id)
    with pytest.raises(Exception):
        update_statut_intervention(
            db_session,
            interv.id,
            StatutIntervention.archivee,
            user_id=user.id,
            remarque="bad",
        )
