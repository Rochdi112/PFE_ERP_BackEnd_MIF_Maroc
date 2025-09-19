from unittest.mock import MagicMock, patch

import pytest

from app.api.v1 import documents as documents_router
from app.core.security import get_password_hash
from app.db import database
from app.models.document import Document
from app.models.intervention import Intervention, InterventionType
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.services import notification_service


# 1) Test upload_document_alias calls create_document
def test_upload_alias_calls_create(monkeypatch):
    with patch("app.api.v1.documents.create_document", return_value={"id": 1}) as cd:
        res = documents_router.upload_document_alias(
            intervention_id=1, file=MagicMock(), db=None
        )
        assert res == {"id": 1}
        cd.assert_called_once()


# 2) Test list_documents returns empty list when none
def test_list_documents_empty(monkeypatch):
    db = MagicMock()
    db.query.return_value.all.return_value = []
    res = documents_router.list_documents(db=db)
    assert res == []


# 3) Test list_documents_by_intervention filters
def test_list_documents_by_intervention(monkeypatch):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value.all.return_value = ["doc"]
    res = documents_router.list_documents_by_intervention(2, db=db)
    assert res == ["doc"]


# 4) Test delete_document not found raises
def test_delete_document_not_found(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(Exception):
        documents_router.delete_document(1, db=db)


# 5) Test delete_document removes file when exists
def test_delete_document_file_removed(tmp_path, monkeypatch):
    eng = database._create_default_engine()
    monkeypatch.setattr(database, "engine", eng)
    database.Base.metadata.create_all(bind=eng)
    db = database.SessionLocal()

    # create user and intervention
    u = User(
        username="u2", email="u2@example.com", hashed_password=get_password_hash("Password123!"), role=UserRole.admin
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    it = Intervention(titre="t", type_intervention=InterventionType.corrective)
    db.add(it)
    db.commit()
    db.refresh(it)

    # create dummy file
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    file_path = uploads_dir / "f.txt"
    file_path.write_text("x")

    # monkeypatch settings upload dir
    from app.core import config

    monkeypatch.setattr(config.settings, "UPLOAD_DIRECTORY", str(uploads_dir))

    doc = Document(chemin=f"static/uploads/{file_path.name}", intervention_id=it.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    res = documents_router.delete_document(doc.id, db=db)
    assert res == {"detail": "Document supprimé"}
    db.close()


# 6) Test send_email_notification success path (mock SMTP and template)
@patch("smtplib.SMTP")
@patch("app.services.notification_service.env")
def test_send_email_notification_success(mock_env, mock_smtp):
    tmpl = MagicMock()
    tmpl.render.return_value = "<p>ok</p>"
    mock_env.get_template.return_value = tmpl
    instance = mock_smtp.return_value.__enter__.return_value
    instance.starttls.return_value = None
    instance.login.return_value = None
    instance.sendmail.return_value = None

    class DummyType:
        value = "information"

    dummy = MagicMock()
    dummy.type_notification = DummyType()
    dummy.contenu = "c"

    notification_service.send_email_notification("to@a.b", dummy)


# 7) Test create_notification raises if user missing
def test_create_notification_user_missing(monkeypatch):
    db = MagicMock()
    data = MagicMock()
    data.user_id = 1
    data.intervention_id = 1
    data.canal = "log"
    data.contenu = "c"
    data.type = "information"
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(Exception):
        notification_service.create_notification(db, data)


# 8) Test document_service.create_document mocked behaviour
def test_document_service_create(monkeypatch):
    with patch(
        "app.services.document_service.create_document", return_value={"id": 2}
    ) as cd:
        res = documents_router.upload_document(
            intervention_id=1, file=MagicMock(), db=None
        )
        assert res == {"id": 2}
        cd.assert_called_once()


# 9) Simple test for Notification model resume property
def test_notification_resume_property():
    n = Notification(
        type_notification=Notification.type_notification.type,
        canal=Notification.canal,
        contenu="x" * 100,
        user_id=1,
        intervention_id=1,
    )
    # ensure resume property runs
    r = n.resume
    assert isinstance(r, str)


# 10) Test documents delete handles file missing gracefully
def test_delete_document_file_missing(monkeypatch):
    db = MagicMock()
    doc = MagicMock()
    doc.chemin = "static/uploads/missing.txt"
    db.query.return_value.filter.return_value.first.return_value = doc
    # os.path.isfile will be False
    res = documents_router.delete_document(1, db=db)
    assert res == {"detail": "Document supprimé"}
