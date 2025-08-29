import pytest
from fastapi import HTTPException
from app.services import intervention_service as svc
from types import SimpleNamespace

class DB:
    def __init__(self, equip=None, tech_exists=True, user_exists=True, intervention=None):
        self._equip = equip
        self._tech_exists = tech_exists
        self._user_exists = user_exists
        self._intervention = intervention
    def query(self, model):
        class Q:
            def __init__(self, parent, model):
                self.parent = parent
                self.model = model
            def filter(self, crit):
                return self
            def first(self):
                # decide based on requested model name
                name = getattr(self.model, '__name__', str(self.model))
                if 'Equipement' in name:
                    return self.parent._equip
                if 'Technicien' in name:
                    return self.parent._tech_exists and SimpleNamespace(id=1)
                if 'User' in name:
                    return self.parent._user_exists and SimpleNamespace(id=1)
                if 'Intervention' in name:
                    return self.parent._intervention
                return None
            def all(self):
                return []
        return Q(self, model)
    def add(self, obj):
        pass
    def commit(self):
        pass
    def refresh(self, obj):
        # simulate created ID
        if hasattr(obj, 'id'):
            return
        obj.id = 999

class Data:
    def __init__(self, technicien_id=None, equipement_id=None):
        self.titre='t'
        self.description='d'
        self.type_intervention='corrective'
        self.statut='ouverte'
        self.priorite='normale'
        self.urgence=False
        self.date_limite=None
        self.technicien_id=technicien_id
        self.equipement_id=equipement_id

def test_create_intervention_missing_equipement():
    db = DB(equip=None)
    data = Data(technicien_id=None, equipement_id=1)
    with pytest.raises(HTTPException):
        svc.create_intervention(db, data, user_id=1)

def test_create_intervention_missing_technicien():
    # technicien_id provided but not found
    db = DB(equip=SimpleNamespace(id=1), tech_exists=False)
    data = Data(technicien_id=5, equipement_id=1)
    with pytest.raises(HTTPException):
        svc.create_intervention(db, data, user_id=1)

def test_update_statut_transition_guards():
    # prepare an intervention object with statut cloturee
    inter = SimpleNamespace(id=1, statut='cloturee')
    db = DB(equip=SimpleNamespace(id=1), intervention=inter, user_exists=True)
    with pytest.raises(HTTPException):
        svc.update_statut_intervention(db, 1, 'en_cours', user_id=1)

def test_update_statut_user_not_found():
    inter = SimpleNamespace(id=2, statut='ouverte')
    db = DB(equip=SimpleNamespace(id=1), intervention=inter, user_exists=False)
    with pytest.raises(HTTPException):
        svc.update_statut_intervention(db, 2, 'en_cours', user_id=999)
