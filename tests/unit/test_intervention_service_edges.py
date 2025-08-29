import pytest
from sqlalchemy.orm import Session
from app.services.intervention_service import create_intervention, update_statut_intervention
from app.schemas.intervention import InterventionCreate, StatutIntervention


def test_create_intervention_missing_equipement(db_session: Session):
    ic = InterventionCreate(
        titre="x",
        description="d",
        type_intervention="corrective",
        statut=StatutIntervention.ouverte,
        priorite="normale",
        urgence=False,
        date_limite=None,
        technicien_id=None,
        equipement_id=99999,
    )
    with pytest.raises(Exception):
        create_intervention(db_session, ic, user_id=1)


def test_update_statut_archivee_forbidden(db_session: Session):
    # create minimal equipment and intervention via direct model to get an id
    from app.models.equipement import Equipement
    from app.models.intervention import Intervention, StatutIntervention as MS
    e = Equipement(nom="E1", type="t", localisation="L", frequence_entretien="7")
    db_session.add(e); db_session.commit(); db_session.refresh(e)
    i = Intervention(titre="i1", description="d", type_intervention="preventive", statut=MS.ouverte, priorite="normale", urgence=False, equipement_id=e.id)
    db_session.add(i); db_session.commit(); db_session.refresh(i)

    # attempt to archive directly without closing
    with pytest.raises(Exception):
        update_statut_intervention(db_session, i.id, StatutIntervention.archivee, user_id=1)


def test_update_statut_missing_user(db_session: Session):
    # create equipment + intervention
    from app.models.equipement import Equipement
    from app.models.intervention import Intervention, StatutIntervention as MS
    e = Equipement(nom="E2", type="t", localisation="L", frequence_entretien="7")
    db_session.add(e); db_session.commit(); db_session.refresh(e)
    i = Intervention(titre="i2", description="d", type_intervention="preventive", statut=MS.ouverte, priorite="normale", urgence=False, equipement_id=e.id)
    db_session.add(i); db_session.commit(); db_session.refresh(i)

    # use a user_id that doesn't exist
    with pytest.raises(Exception):
        update_statut_intervention(db_session, i.id, StatutIntervention.cloturee, user_id=99999)
