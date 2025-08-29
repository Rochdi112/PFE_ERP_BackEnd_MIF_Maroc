import pytest


def test_change_statut_requires_technicien(client, responsable_token, db_session):
    # create a sample intervention as responsable
    from app.services.intervention_service import create_intervention
    from app.schemas.intervention import InterventionCreate, PrioriteIntervention

    # create an equipment first (factory may raise if the equipment already exists)
    from app.tests.utils.factories import create_equipement_helper
    from app.models.equipement import Equipement
    try:
        eq = create_equipement_helper(db_session)
    except Exception:
        eq = db_session.query(Equipement).filter(Equipement.nom == "EQ-FACT").first()
        if not eq:
            raise
    payload = InterventionCreate(
        titre="Test",
        description="desc",
        type="corrective",
        priorite=PrioriteIntervention.normale,
        equipement_id=eq.id
    )
    # create intervention using service directly to bypass permissions
    inter = create_intervention(db_session, payload, user_id=1)
    # try to change statut with responsable token (should be forbidden: technicien required)
    r = client.patch(f"/interventions/{inter.id}/statut", params={"statut": "cloturee"}, headers={"Authorization": f"Bearer {responsable_token}"})
    assert r.status_code in (403, 422, 400)


def test_get_nonexistent_intervention(client, admin_token):
    r = client.get("/interventions/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404
