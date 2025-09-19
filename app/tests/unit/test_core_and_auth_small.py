import pytest
from fastapi import HTTPException
from jose import JWTError

from app.core.security import get_password_hash
from app.core.exceptions import (
    CredentialsException,
    NotFoundException,
    PermissionDeniedException,
)
from app.core.rbac import decode_token, get_current_user
from app.services import auth_service


class DummyDB:
    def __init__(self, user=None):
        self._user = user

    def query(self, model):
        class Q:
            def __init__(self, user):
                self._user = user

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self._user

        return Q(self._user)


class DummyUser:
    def __init__(
        self,
        id=1,
        email="u@example.com",
        hashed_password=get_password_hash("password123!"),
        is_active=True,
        role="admin",
    ):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.role = role
        self.username = "user"


# Exceptions constructors
def test_exceptions_messages():
    ce = CredentialsException()
    assert isinstance(ce, HTTPException)
    nf = NotFoundException("Test")
    assert nf.detail == "Test introuvable"
    pd = PermissionDeniedException()
    assert pd.status_code == 403


# decode_token should raise on invalid token
def test_decode_token_invalid(monkeypatch):
    import app.core.rbac as rbac

    monkeypatch.setattr(
        rbac,
        "jwt",
        type("J", (), {"decode": lambda *a, **k: (_ for _ in ()).throw(JWTError())}),
    )
    with pytest.raises(HTTPException):
        decode_token("bad-token")


# get_current_user fallback when no db user exists
def test_get_current_user_fallback(monkeypatch):
    # token payload with sub and role
    monkeypatch.setattr(
        "app.core.rbac.decode_token", lambda token: {"sub": "42", "role": "responsable"}
    )
    # Use a DummyDB that returns no user -> should now raise 403 instead of returning fallback
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="t", db=DummyDB())
    assert exc.value.status_code == 403


# auth_service error paths
def test_auth_service_invalid_password(monkeypatch):
    dummy = DummyUser()
    db = DummyDB(user=dummy)
    # make verify_password return False
    monkeypatch.setattr(
        "app.services.auth_service.verify_password", lambda pw, hpw: False
    )
    with pytest.raises(HTTPException):
        auth_service.authenticate_user(db, "u@example.com", "bad")


def test_auth_service_disabled_user(monkeypatch):
    dummy = DummyUser(is_active=False)
    db = DummyDB(user=dummy)
    monkeypatch.setattr(
        "app.services.auth_service.verify_password", lambda pw, hpw: True
    )
    with pytest.raises(HTTPException):
        auth_service.authenticate_user(db, "u@example.com", "pwd")
