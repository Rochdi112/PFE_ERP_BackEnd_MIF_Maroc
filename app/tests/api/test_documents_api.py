import io
from fastapi import UploadFile


def test_upload_requires_auth_and_file(client, db_session, admin_token, tmp_upload_dir):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # missing file -> 422
    r = client.post("/documents/upload", data={"intervention_id": 1}, headers=headers)
    assert r.status_code in (401, 422)


def test_upload_and_delete_document_flow(client, db_session, admin_token, tmp_upload_dir):
    from app.services.equipement_service import create_equipement
    from app.schemas.equipement import EquipementCreate
    from app.services.user_service import ensure_user_for_email
    from app.schemas.user import UserRole
    from app.services.intervention_service import create_intervention
    from app.schemas.intervention import InterventionCreate, StatutIntervention

    eq = create_equipement(db_session, EquipementCreate(nom="DOCAPI", type="t", localisation="L", frequence_entretien="7"))
    user = ensure_user_for_email(db_session, email="docapi@example.com", role=UserRole.admin)
    ic = InterventionCreate(titre="docapi", description="d", type_intervention="corrective", statut=StatutIntervention.ouverte, priorite="normale", urgence=False, date_limite=None, technicien_id=None, equipement_id=eq.id)
    interv = create_intervention(db_session, ic, user_id=user.id)

    headers = {"Authorization": f"Bearer {admin_token}"}
    files = {"file": ("t.txt", b"hello")}
    r = client.post(f"/documents/?intervention_id={interv.id}", files=files, headers=headers)
    assert r.status_code in (200, 201)
    j = r.json()
    doc_id = j.get("id")
    # delete
    r2 = client.delete(f"/documents/{doc_id}", headers=headers)
    assert r2.status_code in (200, 200)
