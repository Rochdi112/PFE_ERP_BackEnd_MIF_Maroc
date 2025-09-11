from app.schemas.user import UserCreate, UserRole
from app.services.user_service import create_user, get_user_by_email


def test_create_user_and_fetch(db_session):
    data = UserCreate(
        username="u_unit",
        full_name="Unit U",
        email="u_unit@example.com",
        role=UserRole.client,
        password="Password123!",
    )
    user = create_user(db_session, data)
    assert user.email == "u_unit@example.com"
    fetched = get_user_by_email(db_session, "u_unit@example.com")
    assert fetched is not None
