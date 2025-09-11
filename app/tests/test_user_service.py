from app.db.database import SessionLocal
from app.schemas.user import UserCreate, UserRole
from app.services.user_service import create_user, get_user_by_email


def test_create_and_get_user():
    with SessionLocal() as db:
        data = UserCreate(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            role=UserRole.client,
            password="Secret123456!",
        )
        user = create_user(db, data)
        assert user.id is not None
        fetched = get_user_by_email(db, "test@example.com")
        assert fetched is not None
        assert fetched.email == "test@example.com"
