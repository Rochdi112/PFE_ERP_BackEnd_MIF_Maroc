import pytest
from fastapi import HTTPException

from app.api.v1 import interventions as interventions_module
from app.core.rbac import require_roles


# Test require_roles with dict current_user
def test_require_roles_allows_role_dict(monkeypatch):
    checker = require_roles("admin", "responsable")
    # simulate current_user as dict
    result = checker(current_user={"role": "admin"})
    assert result["role"] == "admin"


def test_require_roles_denies(monkeypatch):
    checker = require_roles("admin")
    with pytest.raises(HTTPException):
        checker(current_user={"role": "technicien"})


# Test create_new_intervention branch where user_id is None ->
# ensure_user_for_email called


class DummyDB:
    def __init__(self):
        self.called = False

    def __getattr__(self, name):
        raise AttributeError


class DummyUser:
    def __init__(self):
        self.user_id = None
        self.email = "test@example.com"
        self.role = "responsable"


def test_create_new_intervention_ensures_user(monkeypatch):
    # monkeypatch ensure_user_for_email to return an object with id
    class Ensured:
        def __init__(self):
            self.id = 123

    monkeypatch.setattr(
        interventions_module, "ensure_user_for_email", lambda db, email, role: Ensured()
    )

    # call the function with data object stub
    class Data:
        titre = "t"
        description = "d"
        type = "corrective"
        statut = "ouverte"
        priorite = "normale"
        urgence = False
        date_limite = None
        technicien_id = None
        equipement_id = 1

    # monkeypatch create_intervention to capture user_id
    called = {}

    def fake_create(db, data, user_id):
        called["user_id"] = user_id
        return {"id": 1}

    monkeypatch.setattr(interventions_module, "create_intervention", fake_create)
    # call with user lacking user_id
    user = {"user_id": None, "email": "test@example.com", "role": "responsable"}
    interventions_module.create_new_intervention(Data(), db=DummyDB(), user=user)
    assert called["user_id"] == 123
