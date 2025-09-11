import pytest
from fastapi import HTTPException

from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserRole, UserUpdate
from app.services.user_service import (
    create_user,
    deactivate_user,
    get_user_by_id,
    reactivate_user,
    update_user,
)


def test_get_user_by_id_not_found():
    with SessionLocal() as db:
        with pytest.raises(HTTPException):
            get_user_by_id(db, 999999)


def test_update_and_activate_deactivate_user():
    with SessionLocal() as db:
        data = UserCreate(
            username="edgeuser",
            full_name="Edge",
            email="edge@example.com",
            role=UserRole.client,
            password="Password123!",
        )
        try:
            user = create_user(db, data)
        except Exception:
            # already exists
            user = db.query(User).filter_by(email="edge@example.com").first()
        assert user is not None, "User should exist"
        updated = update_user(
            db, user.id, UserUpdate(full_name="New Name", password="Newpassword123!")
        )
        assert updated.full_name == "New Name"
        deactivate_user(db, user.id)
        u = db.query(User).filter_by(id=user.id).first()
        assert u is not None
        assert not u.is_active
        reactivate_user(db, user.id)
        u2 = db.query(User).filter_by(id=user.id).first()
        assert u2.is_active
