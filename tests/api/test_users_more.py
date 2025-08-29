import pytest


def test_get_my_profile_missing_user(client):
    # calling /users/me without auth returns 401
    r = client.get("/users/me")
    assert r.status_code in (401, 422)


def test_update_my_profile_not_found(client):
    # create a JWT for a non-existent user and attempt update -> should return 404
    from app.core.security import create_access_token

    fake_token = create_access_token({"sub": "ghost@example.com", "role": "client", "user_id": 9999})
    payload = {"full_name": "No One"}
    r = client.put("/users/update", json=payload, headers={"Authorization": f"Bearer {fake_token}"})
    assert r.status_code == 404
