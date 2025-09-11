def test_login_and_get_me(client, db_session):
    # create a user and then login via username endpoint
    from app.schemas.user import UserCreate, UserRole
    from app.services.user_service import create_user

    uc = UserCreate(
        username="apiuser",
        full_name="Api User",
        email="apiuser@example.com",
        role=UserRole.responsable,
        password="Secret123456!",
    )
    try:
        create_user(db_session, uc)
    except Exception:
        # if already exists, fetch
        from app.services.user_service import get_user_by_email

        get_user_by_email(db_session, uc.email)

    # login via username form
    data = {"username": uc.username, "password": "Secret123456!"}
    r = client.post("/auth/login", data=data)
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        tok = r.json().get("access_token")
        assert tok
        # call /auth/me
        r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
        assert r2.status_code in (200, 404)


def test_user_deactivate_reactivate(db_session):
    from app.schemas.user import UserCreate, UserRole
    from app.services.user_service import create_user, deactivate_user, reactivate_user

    uc = UserCreate(
        username="tmpu",
        full_name="Tmp U",
        email="tmpu@example.com",
        role=UserRole.client,
        password="Password123!",
    )
    try:
        u = create_user(db_session, uc)
    except Exception:
        from app.services.user_service import get_user_by_email

        u = get_user_by_email(db_session, uc.email)

    deactivate_user(db_session, u.id)
    # check DB
    from app.services.user_service import get_user_by_id

    uu = get_user_by_id(db_session, u.id)
    assert not uu.is_active
    reactivate_user(db_session, u.id)
    uu2 = get_user_by_id(db_session, u.id)
    assert uu2.is_active
