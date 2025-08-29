from app.services.auth_service import authenticate_user, authenticate_user_by_username
from app.services.document_service import save_uploaded_file, create_document
from app.db.database import SessionLocal
from app.services.user_service import create_user, ensure_user_for_email
from app.schemas.user import UserCreate, UserRole
from types import SimpleNamespace


def test_authenticate_user_flow():
    with SessionLocal() as db:
        data = UserCreate(username="authuser", full_name="Auth User", email="auth@example.com", role=UserRole.client, password="pw1234")
        try:
            create_user(db, data)
        except Exception:
            pass
        tok = authenticate_user(db, "auth@example.com", "pw1234")
        assert tok.access_token is not None


def test_save_uploaded_file_and_create_document(tmp_path):
    # patch settings.UPLOAD_DIRECTORY to tmp_path
    from app.core.config import settings
    settings.UPLOAD_DIRECTORY = str(tmp_path)

    file_content = b"hello"
    class BytesReader:
        def __init__(self, b: bytes):
            self._b = b
        def read(self):
            return self._b

    fake = SimpleNamespace(filename="test.txt", file=BytesReader(file_content))
    # save_uploaded_file should write file
    path = save_uploaded_file(fake)
    assert path.startswith("static/uploads/")

    # create_document requires an intervention; create a minimal intervention via services
    from app.models.intervention import Intervention
    with SessionLocal() as db:
        # create equipment
        from app.services.equipement_service import create_equipement
        from app.schemas.equipement import EquipementCreate
        eq = create_equipement(db, EquipementCreate(nom="TST-EQ", type="t", localisation="L", frequence_entretien="7"))
        # ensure user
        user = ensure_user_for_email(db, email="docu@example.com", role=UserRole.admin)
        from app.services.intervention_service import create_intervention
        from app.schemas.intervention import InterventionCreate, StatutIntervention
        ic = InterventionCreate(titre="t", description="d", type_intervention="corrective", statut=StatutIntervention.ouverte, priorite="normale", urgence=False, date_limite=None, technicien_id=None, equipement_id=eq.id)
    interv = create_intervention(db, ic, user_id=user.id)
    # recreate a file-like object for create_document (file object reset)
    fake2 = SimpleNamespace(filename="test.txt", file=BytesReader(file_content))
    doc = create_document(db, fake2, intervention_id=interv.id)
    assert doc.id is not None
