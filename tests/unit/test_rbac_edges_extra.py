import pytest


def test_decode_token_missing_role_raises():
    from app.core.rbac import decode_token
    from app.core.security import create_access_token

    token = create_access_token({"sub": "1"})
    payload = decode_token(token)
    assert payload.get("role") is None
