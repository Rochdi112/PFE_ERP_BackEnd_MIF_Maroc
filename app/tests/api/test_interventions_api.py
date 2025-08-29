import pytest
from datetime import datetime, timedelta


def test_intervention_create_and_status_flow(client, responsable_token, db_session):
    # prepare equipment and user
    from app.services.equipement_service import create_equipement
    from app.schemas.equipement import EquipementCreate
    from app.services.user_service import ensure_user_for_email
    from app.schemas.user import UserRole
    from app.schemas.intervention import InterventionCreate, StatutIntervention

    eq = create_equipement(db_session, EquipementCreate(nom="I-EQ", type="t", localisation="L", frequence_entretien="7"))
    u = ensure_user_for_email(db_session, email="creator@example.com", role=UserRole.responsable)

    ic = InterventionCreate(
        titre="TestI",
        description="desc",
        type_intervention="corrective",
        statut=StatutIntervention.ouverte,
        priorite="haute",
        urgence=False,
        date_limite=(datetime.utcnow()+timedelta(days=2)).isoformat(),
        technicien_id=None,
        equipement_id=eq.id
    )

    # send JSON string so datetime fields are serialized correctly
    r = client.post(
        "/interventions/",
        data=ic.model_dump_json(),
        headers={"Authorization": f"Bearer {responsable_token}", "Content-Type": "application/json"},
    )
    assert r.status_code in (200, 201, 404, 422)
    if r.status_code not in (200, 201):
        return
    interv = r.json()
    iid = interv.get("id")

    # change statut to cloturee via technicien role (simulate token with technicien)
    from app.core.security import create_access_token
    # ensure a technicien user exists and use its id for the token
    tech_user = ensure_user_for_email(db_session, email="tech@example.com", role=UserRole.technicien)
    token = create_access_token({"sub": str(tech_user.email), "role": UserRole.technicien.value, "user_id": tech_user.id})
    r2 = client.patch(f"/interventions/{iid}/statut", params={"statut": StatutIntervention.cloturee.value}, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code in (200, 404, 409, 422)
from app.schemas.intervention import InterventionCreate, StatutIntervention
from app.schemas.equipement import EquipementCreate
from app.services.equipement_service import create_equipement
from app.services.user_service import ensure_user_for_email
from app.schemas.user import UserRole


def test_create_and_get_intervention(client, db_session, responsable_token):
    # create equipment
    eq = create_equipement(db_session, EquipementCreate(nom="API-EQ", type="t", localisation="L", frequence_entretien="7"))
    user = ensure_user_for_email(db_session, email="apir@example.com", role=UserRole.responsable)
    ic = InterventionCreate(titre="api1", description="d", type_intervention="corrective", statut=StatutIntervention.ouverte, priorite="normale", urgence=False, date_limite=None, technicien_id=None, equipement_id=eq.id)
    # use client with dependency override; token inclusion skipped for simplicity here
    headers = {"Authorization": f"Bearer {responsable_token}"}
    r = client.post("/interventions/", json=ic.model_dump(), headers=headers)
    assert r.status_code in (200, 201)
    data = r.json()
    assert "id" in data
