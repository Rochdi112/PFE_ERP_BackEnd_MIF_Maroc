def test_ensure_user_for_email_creates_and_retrieves(db_session):
    from app.services.user_service import ensure_user_for_email, get_user_by_email
    from app.schemas.user import UserRole

    email = "unique_test_user@example.com"
    u = ensure_user_for_email(db_session, email=email, role=UserRole.client)
    assert u.email == email
    # ensure retrieving works
    u2 = get_user_by_email(db_session, email)
    assert u2 is not None and u2.email == email


def test_deactivate_and_reactivate_user(db_session):
    from app.services.user_service import ensure_user_for_email, deactivate_user, reactivate_user, get_user_by_email
    from app.schemas.user import UserRole

    email = "temp_user@example.com"
    u = ensure_user_for_email(db_session, email=email, role=UserRole.client)
    deactivate_user(db_session, u.id)
    u2 = get_user_by_email(db_session, email)
    assert not u2.is_active
    reactivate_user(db_session, u.id)
    u3 = get_user_by_email(db_session, email)
    assert u3.is_active
