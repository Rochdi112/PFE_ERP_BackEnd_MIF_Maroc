import pytest


def test_get_user_not_found(client, admin_token):
    # requesting a user id that doesn't exist should return 404
    r = client.get("/users/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404


def test_create_user_invalid_payload(client, admin_token):
    # missing required fields (e.g., password) should return 422
    payload = {"email": "bad@example.com"}
    r = client.post("/users/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 422


def test_deactivate_already_deactivated(client, admin_token, db_session):
    from app.services.user_service import ensure_user_for_email, deactivate_user
    user = ensure_user_for_email(db_session, email="to_deact@example.com", role="responsable")
    # first deactivate
    r1 = client.delete(f"/users/{user.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r1.status_code in (204, 404)
    # second deactivate should still be idempotent (204 or 404 depending on implementation)
    r2 = client.delete(f"/users/{user.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code in (204, 404)

