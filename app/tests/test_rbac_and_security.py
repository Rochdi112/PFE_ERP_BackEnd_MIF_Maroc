from app.core.rbac import decode_token, require_roles
from app.core.security import create_access_token


def test_decode_token_and_require_roles():
    data = {"sub": "1", "role": "admin", "user_id": 1}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload.get("role") == "admin"

    checker = require_roles("admin")
    # Simulate current_user dict
    res = checker(current_user={"user_id": 1, "role": "admin"})
    assert res["role"] == "admin"
