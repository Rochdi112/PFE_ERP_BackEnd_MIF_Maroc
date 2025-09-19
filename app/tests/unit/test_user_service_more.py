from unittest.mock import MagicMock, patch

import pytest

from app.core.security import get_password_hash
from app.db import database
from app.models.user import User, UserRole
from app.services import user_service


def setup_inmemory(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "pytest", object())
    eng = database._create_default_engine()
    monkeypatch.setattr(database, "engine", eng)
    database.Base.metadata.create_all(bind=eng)
    return eng


def test_create_user_conflict_email_and_username(monkeypatch):
    db = MagicMock()
    user_data = MagicMock()
    user_data.email = "a@b.com"
    user_data.username = "u1"
    user_data.password = "pw"
    user_data.full_name = None
    user_data.role = UserRole.client

    # First, simulate existing by email
    db.query.return_value.filter.return_value.first.return_value = True
    with pytest.raises(Exception):
        user_service.create_user(db, user_data)

    # Simulate no email but username exists (fallback returns False)
    db.query.return_value.filter.return_value.first.return_value = None
    with patch(
        "app.services.user_service._check_exists_in_fallback", return_value=True
    ):
        with pytest.raises(Exception):
            user_service.create_user(db, user_data)


def test_ensure_user_for_email_creates_and_gets(monkeypatch):
    setup_inmemory(monkeypatch)
    SessionLocal = database.SessionLocal
    db = SessionLocal()

    # No user exists initially
    res = user_service.get_user_by_email(db, "new@example.com")
    assert res is None

    user = user_service.ensure_user_for_email(db, "new@example.com", UserRole.client)
    assert user.email == "new@example.com"
    assert user.username.startswith("new")

    # ensure idempotent: calling again returns same user
    user2 = user_service.ensure_user_for_email(db, "new@example.com", UserRole.client)
    assert user2.id == user.id
    db.close()


def test_update_deactivate_reactivate(monkeypatch):
    setup_inmemory(monkeypatch)
    db = database.SessionLocal()
    u = User(
        username="x",
        email="x@example.com",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.client,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    class UD:
        pass

    ud = UD()
    ud.full_name = "New Name"
    ud.password = "Newpassword123!"

    # capture old hash before update
    old_hash = u.hashed_password
    updated = user_service.update_user(db, u.id, ud)
    assert updated.full_name == "New Name"
    assert updated.hashed_password != old_hash

    user_service.deactivate_user(db, u.id)
    assert db.query(User).filter(User.id == u.id).first().is_active is False

    user_service.reactivate_user(db, u.id)
    assert db.query(User).filter(User.id == u.id).first().is_active is True
    db.close()


def test_database_create_engine_fallback(monkeypatch):
    # Simulate absence of pytest in sys.modules so function tries create_engine
    monkeypatch.delitem(__import__("sys").modules, "pytest", raising=False)
    # Force sqlalchemy.create_engine to raise to trigger fallback
    import sqlalchemy

    real_create = sqlalchemy.create_engine

    def fake_create(url, *a, **kw):
        raise Exception("fail")

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create)
    try:
        eng = database._create_default_engine()
        assert eng is not None
        assert eng.url.get_backend_name() == "postgresql"
    finally:
        monkeypatch.setattr(sqlalchemy, "create_engine", real_create)
