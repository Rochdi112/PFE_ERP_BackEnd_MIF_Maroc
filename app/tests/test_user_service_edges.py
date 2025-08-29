import pytest
from app.db.database import SessionLocal
from app.services.user_service import get_user_by_id, update_user, deactivate_user, reactivate_user, create_user
from app.schemas.user import UserCreate, UserRole, UserUpdate
from fastapi import HTTPException


def test_get_user_by_id_not_found():
    with SessionLocal() as db:
        with pytest.raises(HTTPException):
            get_user_by_id(db, 999999)


def test_update_and_activate_deactivate_user():
    with SessionLocal() as db:
        data = UserCreate(username="edgeuser", full_name="Edge", email="edge@example.com", role=UserRole.client, password="pwd")
        try:
            user = create_user(db, data)
        except Exception:
            # already exists
            user = db.query(type(data)).first()  # fallback
        updated = update_user(db, user.id, UserUpdate(full_name="New Name", password="newpwd"))
        assert updated.full_name == "New Name"
        deactivate_user(db, user.id)
        u = db.query(type(user)).filter_by(id=user.id).first()
        assert u is not None
        assert not u.is_active
        reactivate_user(db, user.id)
        u2 = db.query(type(user)).filter_by(id=user.id).first()
        assert u2.is_active
