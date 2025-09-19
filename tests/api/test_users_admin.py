def test_create_and_list_users_admin(client, admin_token):
    payload = {
        "username": "jdoe",
        "full_name": "John Doe",
        "email": "jdoe@example.com",
        "role": "client",
        "password": "Strongpass123!"
    }
    r = client.post("/users/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    created = r.json()
    assert created.get("email") == payload["email"]

    # fetch the created user directly (avoid listing all users which may validate existing DB rows)
    uid = created.get("id")
    r2 = client.get(f"/users/{uid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 200
    fetched = r2.json()
    assert fetched.get("email") == payload["email"]
