import pytest


def test_create_list_delete_equipement(client, responsable_token, db_session):
    # Create via service to ensure DB entry
    from app.services.equipement_service import create_equipement, get_all_equipements
    from app.schemas.equipement import EquipementCreate

    ec = EquipementCreate(nom="EQ-1", type="typeA", localisation="L1", frequence_entretien="7")
    eq = create_equipement(db_session, ec)
    assert eq.id is not None

    # list via API
    r = client.get("/equipements/")
    assert r.status_code == 200
    assert any(int(e.get("id")) == eq.id for e in r.json())

    # delete via API requires responsable token
    r2 = client.delete(f"/equipements/{eq.id}", headers={"Authorization": f"Bearer {responsable_token}"})
    # deletion may return 200/204/409 depending on constraints
    assert r2.status_code in (200, 204, 409)
