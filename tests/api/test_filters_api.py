import pytest
from app.services.equipement_service import create_equipement
from app.schemas.equipement import EquipementCreate
from app.services.intervention_service import create_intervention
from app.schemas.intervention import InterventionCreate, StatutIntervention


def test_filter_by_statut_and_urgence(client, responsable_token, db_session):
    # prepare equipment and interventions
    eq = create_equipement(db_session, EquipementCreate(nom="F-EQ", type="t", localisation="L", frequence_entretien="7"))
    ic1 = InterventionCreate(titre="f1", description="d", type_intervention="corrective", statut=StatutIntervention.ouverte, priorite="normale", urgence=True, date_limite=None, technicien_id=None, equipement_id=eq.id)
    ic2 = InterventionCreate(titre="f2", description="d", type_intervention="preventive", statut=StatutIntervention.cloturee, priorite="normale", urgence=False, date_limite=None, technicien_id=None, equipement_id=eq.id)
    create_intervention(db_session, ic1, user_id=1)
    create_intervention(db_session, ic2, user_id=1)

    r = client.get("/filters/interventions", params={"statut": StatutIntervention.ouverte.value}, headers={"Authorization": f"Bearer {responsable_token}"})
    assert r.status_code == 200
    data = r.json()
    assert any(item["titre"] == "f1" for item in data)
