from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1 import documents as documents_router
from app.services import notification_service, technicien_service


def test_create_technicien_user_missing():
    db = MagicMock()
    data = MagicMock()
    data.user_id = 1
    data.equipe = "A"
    data.disponibilite = "disponible"
    data.competences_ids = None
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException):
        technicien_service.create_technicien(db, data)


def test_create_technicien_user_not_technicien():
    db = MagicMock()
    user = MagicMock()
    user.role = "client"
    db.query.return_value.filter.return_value.first.return_value = user
    data = MagicMock()
    data.user_id = 1
    data.equipe = "A"
    data.disponibilite = "disponible"
    data.competences_ids = None
    with pytest.raises(HTTPException):
        technicien_service.create_technicien(db, data)


def test_create_competence_duplicate():
    db = MagicMock()
    data = MagicMock()
    data.nom = "elec"
    db.query.return_value.filter.return_value.first.return_value = True
    with pytest.raises(HTTPException):
        technicien_service.create_competence(db, data)


def test_create_competence_success(monkeypatch):
    db = MagicMock()
    data = MagicMock()
    data.nom = "plomberie"
    db.query.return_value.filter.return_value.first.return_value = None

    # emulate DB adding -> id
    def add_commit_refresh(obj):
        obj.id = 1

    db.add.side_effect = lambda o: None
    db.commit.side_effect = lambda: None
    db.refresh.side_effect = lambda o: setattr(o, "id", 1)
    res = technicien_service.create_competence(db, data)
    assert res.id == 1


def test_delete_document_exception_ignored(monkeypatch):
    # prepare doc that causes os.path.isfile to raise
    doc = MagicMock()
    doc.chemin = "static/uploads/badfile.txt"
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = doc
    # make os.path.isfile raise
    monkeypatch.setattr(
        "os.path.isfile", lambda x: (_ for _ in ()).throw(Exception("boom"))
    )
    res = documents_router.delete_document(document_id=1, db=db)
    assert res["detail"] == "Document supprimé"


def test_send_email_notification_success(monkeypatch):
    # ensure that send_email_notification handles success path
    from app.services.notification_service import send_email_notification

    class DT:
        value = "information"

    n = MagicMock()
    n.type_notification = DT()
    n.contenu = "c"

    class DummyTmpl:
        def render(self, **k):
            return "<p>x</p>"

    monkeypatch.setattr(
        notification_service, "env", MagicMock(get_template=lambda x: DummyTmpl())
    )
    monkeypatch.setattr(
        "smtplib.SMTP",
        lambda h, p: MagicMock(
            __enter__=lambda s: s,
            starttls=lambda: None,
            login=lambda u, p: None,
            sendmail=lambda f, t, m: None,
        ),
    )
    send_email_notification("a@b.com", n)


def test_get_all_techniciens_calls_db():
    db = MagicMock()
    db.query.return_value.all.return_value = ["t1"]
    res = technicien_service.get_all_techniciens(db)
    assert res == ["t1"]


def test_get_all_competences_calls_db():
    db = MagicMock()
    db.query.return_value.all.return_value = ["c1"]
    res = technicien_service.get_all_competences(db)
    assert res == ["c1"]


def test_get_technicien_by_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException):
        technicien_service.get_technicien_by_id(db, 1)
