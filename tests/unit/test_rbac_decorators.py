from app.core.rbac import require_roles
import pytest


def test_require_roles_allows_dict_user():
    checker = require_roles("admin", "responsable")
    # Simulate FastAPI passing a dict user
    user = {"role": "admin", "email": "a@e.com"}
    result = checker(current_user=user)
    assert result == user


def test_require_roles_denies_wrong_role():
    checker = require_roles("technicien")
    user = {"role": "responsable"}
    with pytest.raises(Exception):
        checker(current_user=user)

