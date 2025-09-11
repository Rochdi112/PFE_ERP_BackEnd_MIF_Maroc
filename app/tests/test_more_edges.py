from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.v1.documents import delete_document
from app.core.security import create_access_token, verify_token
from app.db.database import SessionLocal
from app.main import app
from app.models.user import User
from app.schemas.equipement import EquipementCreate
from app.schemas.intervention import InterventionCreate, StatutIntervention
from app.schemas.user import UserCreate, UserRole
from app.services.auth_service import authenticate_user
from app.services.equipement_service import create_equipement
from app.services.intervention_service import create_intervention
from app.services.user_service import create_user, ensure_user_for_email

client = TestClient(app)


def test_authenticate_user_wrong_password_raises():
    with SessionLocal() as db:
        data = UserCreate(
            username="pwuser",
            full_name="PW",
            email="pw@example.com",
            role=UserRole.client,
            password="Password123!",
        )
        try:
            create_user(db, data)
        except Exception:
            pass
        with pytest.raises(Exception):
                        authenticate_user(db, "pw@example.com", "Password123")


def test_auth_me_endpoint_returns_user():
    with SessionLocal() as db:
        data = UserCreate(
            username="meuser",
            full_name="Me",
            email="me@example.com",
            role=UserRole.responsable,
            password="Mpass123456!",
        )
        try:
            u = create_user(db, data)
        except Exception:
            u = db.query(User).filter_by(email="me@example.com").first()
        token = create_access_token(
            {"sub": u.email, "role": u.role.value, "user_id": u.id}
        )
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        j = r.json()
        assert j.get("email") == "me@example.com"


def test_equipement_delete_conflict_when_interventions_exist():
    with SessionLocal() as db:
        eq = create_equipement(
            db,
            EquipementCreate(
                nom="DELTEST", type="t", localisation="L", frequence_entretien="7"
            ),
        )
        user = ensure_user_for_email(
            db, email="dconf@example.com", role=UserRole.responsable
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
        create_intervention(db, ic, user_id=user.id)
        # Attempting to delete should raise HTTPException (409)
        from fastapi import HTTPException

        from app.services.equipement_service import delete_equipement

        with pytest.raises(HTTPException):
            delete_equipement(db, eq.id)


def test_delete_document_service_function_removes_file_and_db(tmp_path):
    from app.core.config import settings

    settings.UPLOAD_DIRECTORY = str(tmp_path)
    file_content = b"abc"

    class BytesReader:
        def __init__(self, b: bytes):
            self._b = b

        def read(self):
            return self._b

    fake = SimpleNamespace(filename="f.txt", file=BytesReader(file_content))
    with SessionLocal() as db:
        eq = create_equipement(
            db,
            EquipementCreate(
                nom="DOC-EQ", type="t", localisation="L", frequence_entretien="7"
            ),
        )
        user = ensure_user_for_email(
            db, email="docdel@example.com", role=UserRole.admin
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
        interv = create_intervention(db, ic, user_id=user.id)
        # create_document expects UploadFile-like; our fake has .file
        from app.services.document_service import create_document as svc_create

        doc = svc_create(db, fake, intervention_id=interv.id)
        # Ensure file exists
        import os

        fname = doc.chemin.split("/")[-1]
        abs_path = os.path.join(settings.UPLOAD_DIRECTORY, fname)
        assert os.path.exists(abs_path)
        # Call delete_document endpoint function directly (bypass RBAC)
        res = delete_document(document_id=doc.id, db=db)
        assert res.get("detail") == "Document supprimé"
        assert not os.path.exists(abs_path)


def test_verify_token_invalid_raises():
    with pytest.raises(Exception):
        verify_token("not.a.token")
