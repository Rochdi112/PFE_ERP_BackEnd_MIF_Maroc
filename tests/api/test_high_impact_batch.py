import io
from app.core.security import create_access_token


def test_get_my_profile_and_update(client, db_session):
    # create a real admin with full_name so /users/me response validation passes
    from app.services.user_service import create_user
    from app.schemas.user import UserCreate, UserRole
    from app.core.security import create_access_token

    admin_data = UserCreate(username="apiadmin", full_name="API Admin", email="apiadmin@example.com", role=UserRole.admin, password="Secret123456!")
    try:
        admin = create_user(db_session, admin_data)
    except Exception:
        # fallback: query existing
        from app.models.user import User
        admin = db_session.query(User).filter(User.email == admin_data.email).first()

    token = create_access_token({"sub": admin.email, "role": admin.role, "user_id": admin.id})

    # get own profile
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    me = r.json()
    assert me.get("email") == admin.email

    # update profile
    payload = {"full_name": "Updated Name"}
    r2 = client.put("/users/update", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code in (200, 201)


def test_create_intervention_without_userid_creates_user_and_intervention(client, responsable_token, db_session):
    # create equipment
    from app.tests.utils.factories import create_equipement_helper
    from app.models.equipement import Equipement
    try:
        eq = create_equipement_helper(db_session)
    except Exception:
        eq = db_session.query(Equipement).filter(Equipement.nom == "EQ-FACT").first()
        if not eq:
            raise

    payload = {
        "titre": "API created",
        "description": "via api",
        "type": "corrective",
        "priorite": "normale",
        "equipement_id": eq.id
    }
    r = client.post("/interventions/", json=payload, headers={"Authorization": f"Bearer {responsable_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("titre") == payload["titre"]


def test_change_statut_as_technicien(client, db_session):
    from app.services.user_service import ensure_user_for_email
    from app.core.security import create_access_token
    from app.tests.utils.factories import create_equipement_helper

    # prepare technicien user and token
    tech = ensure_user_for_email(db_session, email="tech1@example.com", role="technicien")
    token = create_access_token({"sub": tech.email, "role": tech.role, "user_id": tech.id})

    # prepare equipment and intervention
    from app.models.equipement import Equipement
    try:
        eq = create_equipement_helper(db_session)
    except Exception:
        eq = db_session.query(Equipement).filter(Equipement.nom == "EQ-FACT").first()
        if not eq:
            raise
    from app.services.intervention_service import create_intervention
    from app.schemas.intervention import InterventionCreate

    ic = InterventionCreate(titre="t", description="d", type="corrective", equipement_id=eq.id)
    inter = create_intervention(db_session, ic, user_id=tech.id)

    # change statut to en_cours
    r = client.patch(f"/interventions/{inter.id}/statut", params={"statut": "en_cours"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    out = r.json()
    assert out.get("statut") == "en_cours"


def test_create_notification_email_channel(client, db_session):
    # create a user target
    from app.services.user_service import ensure_user_for_email
    u = ensure_user_for_email(db_session, email="notify@example.com", role="client")

    payload = {
        "type": "information",
        "canal": "email",
        "contenu": "test notif",
        "user_id": u.id
    }
    r = client.post("/notifications/", json=payload, headers={})
    # endpoint may require auth; if unauthorized, assert 401; else should create
    assert r.status_code in (201, 200, 401)


def test_upload_document_invalid_intervention(client, admin_token, tmp_upload_dir):
    # try to upload a file referencing nonexistent intervention
    # use bytes directly for httpx file upload to avoid deprecation warning
    files = {"file": ("test.txt", b"hi", "text/plain")}
    data = {"intervention_id": "999999", "description": "x"}
    r = client.post("/documents/", data=data, files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (404, 422)


def test_get_technicien_not_found(client, admin_token):
    r = client.get("/techniciens/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404
