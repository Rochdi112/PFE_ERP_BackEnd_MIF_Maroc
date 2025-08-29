import pytest
from app.services.auth_service import authenticate_user
from app.services.user_service import create_user
from app.schemas.user import UserCreate, UserRole


def test_authenticate_wrong_credentials(db_session):
    data = UserCreate(username="aw1", full_name="A W", email="aw1@example.com", role=UserRole.client, password="right")
    try:
        create_user(db_session, data)
    except Exception:
        pass
    with pytest.raises(Exception):
        authenticate_user(db_session, "aw1@example.com", "bad")


def test_authenticate_disabled_account(db_session):
    u = create_user(db_session, UserCreate(username="aw2", full_name="A W2", email="aw2@example.com", role=UserRole.client, password="pwd"))
    # disable
    u.is_active = False
    db_session.commit()
    with pytest.raises(Exception):
        authenticate_user(db_session, u.email, "pwd")
