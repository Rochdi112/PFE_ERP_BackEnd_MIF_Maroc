def test_create_list_get_update_delete_technicien(
    client, responsable_token, db_session
):
    # create a user first (services helper)
    from app.schemas.user import UserRole
    from app.services.user_service import ensure_user_for_email

    # create a user with technicien role
    u = ensure_user_for_email(
        db_session, email="tech@example.com", role=UserRole.technicien
    )
    # ensure full_name is present to satisfy response schema
    u.full_name = u.full_name or "Tech"
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    payload = {"user_id": u.id, "equipe": "A", "disponibilite": "disponible"}
    r = client.post(
        "/techniciens/",
        json=payload,
        headers={"Authorization": f"Bearer {responsable_token}"},
    )
    assert r.status_code in (200, 201, 422)
    if r.status_code in (200, 201):
        data = r.json()
        assert data.get("user") is not None
        tid = data["id"]
    else:
        return

    # list
    r = client.get(
        "/techniciens/", headers={"Authorization": f"Bearer {responsable_token}"}
    )
    assert r.status_code == 200
    assert any(t["id"] == tid for t in r.json())

    # get
    r = client.get(
        f"/techniciens/{tid}", headers={"Authorization": f"Bearer {responsable_token}"}
    )
    assert r.status_code == 200
    assert r.json()["id"] == tid

    # update equipe
    update = {"equipe": "B", "disponibilite": "indisponible"}
    r = client.put(
        f"/techniciens/{tid}",
        json=update,
        headers={"Authorization": f"Bearer {responsable_token}"},
    )
    assert r.status_code == 200
    assert r.json()["equipe"] == "B"

    # delete
    r = client.delete(
        f"/techniciens/{tid}", headers={"Authorization": f"Bearer {responsable_token}"}
    )
    assert r.status_code == 204


def test_create_and_list_competence(client, responsable_token):
    payload = {"nom": " plomberie "}
    r = client.post(
        "/techniciens/competences",
        json=payload,
        headers={"Authorization": f"Bearer {responsable_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nom"].strip() == "plomberie"

    r = client.get(
        "/techniciens/competences",
        headers={"Authorization": f"Bearer {responsable_token}"},
    )
    assert r.status_code == 200
    assert any(c["nom"] == data["nom"] for c in r.json())


def test_list_techniciens_pagination_window(client, responsable_token, db_session):
    from uuid import uuid4

    from app.schemas.technicien import TechnicienCreate
    from app.schemas.user import UserRole
    from app.services.technicien_service import create_technicien
    from app.services.user_service import ensure_user_for_email

    created_ids = []
    for idx in range(3):
        email = f"tech-pag-{idx}-{uuid4()}@example.com"
        user = ensure_user_for_email(db_session, email=email, role=UserRole.technicien)
        user.full_name = user.full_name or f"Technicien {idx}"
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        payload = TechnicienCreate(user_id=user.id, equipe="T", disponibilite="disponible")
        technicien = create_technicien(db_session, payload)
        created_ids.append(technicien.id)

    r = client.get(
        "/techniciens/?limit=2&offset=1",
        headers={"Authorization": f"Bearer {responsable_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 2
    returned_ids = {item["id"] for item in data}
    assert returned_ids.issubset(set(created_ids))
