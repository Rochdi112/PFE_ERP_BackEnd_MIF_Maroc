from types import SimpleNamespace
from app.services.equipement_service import create_equipement
from app.schemas.equipement import EquipementCreate
from app.db.database import SessionLocal


def test_create_duplicate_equipement_raises():
    with SessionLocal() as db:
        data = EquipementCreate(nom="DUP", type="t", localisation="L", frequence_entretien="7")
        e1 = create_equipement(db, data)
        try:
            create_equipement(db, data)
            raised = False
        except Exception:
            raised = True
        assert raised


def test_save_uploaded_file_no_extension_raises(tmp_path):
    from app.core.config import settings
    settings.UPLOAD_DIRECTORY = str(tmp_path)
    class BytesReader:
        def __init__(self, b: bytes):
            self._b = b
        def read(self):
            return self._b

    fake = SimpleNamespace(filename="nofile", file=BytesReader(b"x"))
    try:
        from app.services.document_service import save_uploaded_file
        save_uploaded_file(fake)
        ok = True
    except Exception:
        ok = False
    assert not ok
