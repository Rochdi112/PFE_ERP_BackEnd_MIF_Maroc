import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import SessionLocal, get_db
from app.main import app


@pytest.fixture(scope="function")
def db_session():
    """Provides a SQLAlchemy session for tests.

    Uses in-memory SQLite when pytest is running.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    """Provides a TestClient that overrides the FastAPI get_db dependency.

    Uses the test session.
    """

    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    # Override dependency
    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def tmp_upload_dir(tmp_path, monkeypatch):
    """Point settings.UPLOAD_DIRECTORY to a temporary directory for file tests."""
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))
    return tmp_path


@pytest.fixture(scope="function")
def admin_token(db_session):
    from app.core.security import create_access_token
    from app.schemas.user import UserRole
    from app.services.user_service import ensure_user_for_email

    u = ensure_user_for_email(
        db_session, email="admin@example.com", role=UserRole.admin
    )
    token = create_access_token({"sub": u.email, "role": u.role.value, "user_id": u.id})
    return token


@pytest.fixture(scope="function")
def responsable_token(db_session):
    from app.core.security import create_access_token
    from app.schemas.user import UserRole
    from app.services.user_service import ensure_user_for_email

    u = ensure_user_for_email(
        db_session, email="resp@example.com", role=UserRole.responsable
    )
    token = create_access_token({"sub": u.email, "role": u.role.value, "user_id": u.id})
    return token
