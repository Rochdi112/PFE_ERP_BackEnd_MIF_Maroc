import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1 import documents as documents_router
from app.core import security
from app.core.config import settings
from app.db import database
from app.models.equipement import Equipement
from app.schemas.planning import PlanningCreate
from app.services import planning_service, user_service


def test_upload_document_calls_service(monkeypatch):
    with patch("app.api.v1.documents.create_document", return_value={"id": 1}) as cd:
        res = documents_router.upload_document(
            intervention_id=1, file=MagicMock(), db=MagicMock()
        )
        assert res == {"id": 1}
        cd.assert_called_once()


def test_upload_document_alias_calls_service(monkeypatch):
    with patch("app.api.v1.documents.create_document", return_value={"id": 2}) as cd:
        res = documents_router.upload_document_alias(
            intervention_id=1, file=MagicMock(), db=MagicMock()
        )
        assert res == {"id": 2}
        cd.assert_called_once()


def test_list_documents_returns_all():
    db = MagicMock()
    db.query.return_value.all.return_value = ["d1", "d2"]
    res = documents_router.list_documents(db=db)
    assert res == ["d1", "d2"]


def test_list_documents_by_intervention_filters():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value.all.return_value = ["d"]
    res = documents_router.list_documents_by_intervention(intervention_id=5, db=db)
    assert res == ["d"]


def test_delete_document_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException):
        documents_router.delete_document(document_id=1, db=db)


def test_delete_document_file_removed(tmp_path, monkeypatch):
    # prepare a fake file in upload dir
    up = tmp_path / "uploads"
    up.mkdir()
    f = up / "file.txt"
    f.write_text("x")

    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(up))
    # create fake doc with chemin
    doc = MagicMock()
    doc.chemin = "static/uploads/file.txt"
    doc.id = 1
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = doc

    res = documents_router.delete_document(document_id=1, db=db)
    # file should be removed
    assert not f.exists()
    db.delete.assert_called_once_with(doc)
    assert res["detail"] == "Document supprimé"


def test_notification_send_email_success(monkeypatch):
    # ensure template exists and SMTP succeeds
    from app.services.notification_service import send_email_notification

    class DummyType:
        value = "information"

    dummy = MagicMock()
    dummy.type_notification = DummyType()
    dummy.contenu = "hello"

    with (
        patch("app.services.notification_service.env") as mock_env,
        patch("smtplib.SMTP") as mock_smtp,
    ):
        tmpl = MagicMock()
        tmpl.render.return_value = "<p>ok</p>"
        mock_env.get_template.return_value = tmpl
        instance = mock_smtp.return_value.__enter__.return_value
        instance.starttls.return_value = None
        instance.login.return_value = None
        instance.sendmail.return_value = None
        # Should not raise
        send_email_notification("a@b.com", dummy)


def test_create_planning_success(monkeypatch):
    # setup in-memory DB and create equipment
    monkeypatch.setitem(__import__("sys").modules, "pytest", object())
    eng = database._create_default_engine()
    monkeypatch.setattr(database, "engine", eng)
    database.Base.metadata.create_all(bind=eng)
    db = database.SessionLocal()
    # Equipement requires non-null 'type_equipement' and 'localisation'
    eq = Equipement(nom="E", type="generic", localisation="site A")
    db.add(eq)
    db.commit()
    db.refresh(eq)

    data = PlanningCreate(
        frequence="mensuel",
        prochaine_date=datetime.utcnow(),
        derniere_date=None,
        equipement_id=eq.id,
    )
    planning = planning_service.create_planning(db, data)
    assert planning.equipement_id == eq.id
    db.close()


def test_get_current_user_missing_sub_raises():
    # create token without sub
    token = security.create_access_token({"email": "a@b.com"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    # payload missing 'sub' should trigger HTTPException
    with pytest.raises(HTTPException):
        asyncio.run(security.get_current_user(creds))


def test_get_user_by_id_fallback_raises(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    # make SessionLocal raise when used
    monkeypatch.setattr(
        user_service, "SessionLocal", lambda: (_ for _ in ()).throw(Exception("boom"))
    )
    with pytest.raises(HTTPException):
        user_service.get_user_by_id(db, 999)
