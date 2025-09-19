from uuid import uuid4

from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserRole
from app.services.user_service import create_user


def test_role_change_revokes_admin_access(client, db_session):
    unique = uuid4().hex[:8]
    email = f"rbac-admin-{unique}@example.com"
    user_data = UserCreate(
        username=f"rbac_admin_{unique}",
        full_name="RBAC Admin",
        email=email,
        role=UserRole.admin,
        password="ChangeMe123!",
    )
    admin = create_user(db_session, user_data)

    token = create_access_token(
        {"sub": admin.email, "role": admin.role.value, "user_id": admin.id}
    )
    headers = {"Authorization": f"Bearer {token}"}

    first = client.get(f"/users/{admin.id}", headers=headers)
    assert first.status_code == 200

    admin.role = UserRole.client
    db_session.commit()
    db_session.refresh(admin)

    forbidden = client.get(f"/users/{admin.id}", headers=headers)
    assert forbidden.status_code == 403
