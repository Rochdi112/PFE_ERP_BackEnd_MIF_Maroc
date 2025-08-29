import pytest
from types import SimpleNamespace
from fastapi import HTTPException

# rbac tests
from app.core.rbac import require_roles, get_current_user

class DummyDB:
    def query(self, *a, **k):
        class Q:
            def filter(self, *a, **k):
                return self
            def first(self):
                return None
        return Q()

def test_require_roles_with_object_user():
    checker = require_roles('technicien')
    user_obj = SimpleNamespace(role='technicien')
    res = checker(current_user=user_obj)
    assert res is user_obj

def test_get_current_user_missing_role_raises(monkeypatch):
    # simulate decode_token returning payload without role
    monkeypatch.setattr('app.core.rbac.decode_token', lambda token: {'sub': '1'})
    with pytest.raises(HTTPException):
        get_current_user(token='t', db=DummyDB())

# interventions: test change_statut_intervention ensures ensure_user_for_email called when no user_id
from app.api.v1 import interventions as interventions_mod

def test_change_statut_ensures_user(monkeypatch):
    class Ensured:
        def __init__(self):
            self.id = 555
    # patch ensure_user_for_email
    monkeypatch.setattr(interventions_mod, 'ensure_user_for_email', lambda db, email, role: Ensured())
    # patch update_statut_intervention to capture user_id
    captured = {}
    def fake_update(db, intervention_id, new_statut, user_id, remarque):
        captured['user_id'] = user_id
        return {'id': intervention_id}
    monkeypatch.setattr(interventions_mod, 'update_statut_intervention', fake_update)
    user = {'user_id': None, 'email': 'a@b.c', 'role': 'technicien'}
    res = interventions_mod.change_statut_intervention(1, 'ouverte', remarque='ok', db=DummyDB(), user=user)
    assert captured.get('user_id') == 555

# notifications: list with filters and delete behavior
from app.api.v1 import notifications as notifications_mod

class Q:
    def __init__(self, items):
        self.items = items
        self.filters = []
    def filter(self, crit):
        self.filters.append(crit)
        return self
    def offset(self, o):
        return self
    def limit(self, l):
        return self
    def all(self):
        return self.items
    def first(self):
        return self.items[0] if self.items else None

class DBWithNotifications:
    def __init__(self, items):
        self._items = items
    def query(self, model):
        return Q(self._items)

def test_list_notifications_filters():
    items = [{'id':1}, {'id':2}]
    db = DBWithNotifications(items)
    res = notifications_mod.list_notifications(db=db, user_id=10, intervention_id=20, limit=10, offset=0)
    assert res == items

def test_delete_notification_not_found():
    db = DBWithNotifications([])
    with pytest.raises(HTTPException):
        notifications_mod.delete_notification(999, db=db)

def test_delete_notification_success():
    items = [{'id': 2}]
    class Notif:
        def __init__(self):
            self.id = 2
    # create a DB that returns an object for first()
    class DB2:
        def query(self, model):
            class Q2:
                def filter(self, *a, **k):
                    return self
                def first(self):
                    return Notif()
            return Q2()
        def delete(self, obj):
            self.deleted = True
        def commit(self):
            self.committed = True
    db2 = DB2()
    res = notifications_mod.delete_notification(2, db=db2)
    assert res == {"detail": "Notification supprimée"}
