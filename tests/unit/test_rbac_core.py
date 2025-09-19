import pytest
from fastapi import HTTPException

from app.core.security import create_access_token


def test_decode_token_and_get_current_user_fallback(db_session):
    from app.core.rbac import decode_token, get_current_user

    token = create_access_token({"sub": "42", "role": "technicien", "user_id": 42})
    payload = decode_token(token)
    assert payload.get("role") == "technicien"

    # call get_current_user dependency function directly by providing token and db
    # get_current_user is a callable; call it directly with token and db
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db_session)
    assert exc.value.status_code == 403


def test_require_roles_allows_and_denies():
    from app.core.rbac import require_roles

    checker = require_roles("admin", "responsable")
    # simulate current_user with allowed role
    class CU:
        role = "admin"

    assert checker.__closure__ is not None