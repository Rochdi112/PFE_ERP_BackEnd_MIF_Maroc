import pytest
from datetime import datetime, timedelta
from app.services import planning_service
from unittest.mock import MagicMock
from app.models.planning import FrequencePlanning


def make_db_with_planning(monkeypatch, tmp_path):
    # Use the in-memory sqlite engine via the central database module
    from app.db import database
    monkeypatch.setitem(__import__('sys').modules, 'pytest', object())
    eng = database._create_default_engine()
    monkeypatch.setattr(database, 'engine', eng)
    # Ensure models imported and schema created
    from app.models import planning as mplanning
    # create a planning via model directly
    sess = database.SessionLocal()
    return sess


def test_create_planning_invalid_equipement(monkeypatch):
    # db mock that returns None for equipement
    db = MagicMock()
    data = MagicMock()
    data.equipement_id = 999
    data.frequence = 'mensuel'
    data.prochaine_date = datetime.utcnow()
    data.derniere_date = None

    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(Exception):
        planning_service.create_planning(db, data)


def test_create_planning_invalid_frequency(monkeypatch):
    db = MagicMock()
    eq = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = eq
    data = MagicMock()
    data.equipement_id = 1
    data.frequence = 'invalide'
    data.prochaine_date = datetime.utcnow()
    data.derniere_date = None
    with pytest.raises(Exception):
        planning_service.create_planning(db, data)


def test_update_planning_dates_and_frequence(monkeypatch):
    # Create a fake planning object
    class P:
        def __init__(self):
            self.id = 1
            self.prochaine_date = datetime.utcnow()
            self.derniere_date = None
            self.frequence = FrequencePlanning.mensuel
    p = P()
    db = MagicMock()
    # get_planning_by_id will be called - patch it
    monkeypatch.setattr(planning_service, 'get_planning_by_id', lambda db, pid: p)
    new_date = datetime.utcnow() + timedelta(days=10)
    res = planning_service.update_planning_dates(db, 1, new_date)
    assert res.prochaine_date == new_date

    res2 = planning_service.update_planning_frequence(db, 1, 'hebdomadaire')
    assert res2.frequence == FrequencePlanning.hebdomadaire


def test_delete_planning_calls_delete(monkeypatch):
    p = MagicMock()
    db = MagicMock()
    monkeypatch.setattr(planning_service, 'get_planning_by_id', lambda db, pid: p)
    planning_service.delete_planning(db, 1)
    db.delete.assert_called_once_with(p)
    db.commit.assert_called_once()


# Tests for filters
from app.api.v1 import filters as filters_module
from app.models.intervention import StatutIntervention, InterventionType


def test_filter_interventions_calls_filters(monkeypatch):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.all.return_value = ['a']
    res = filters_module.filter_interventions(statut=StatutIntervention.cloturee, urgence=True, type=InterventionType.corrective, technicien_id=1, db=db, user={'id':1})
    assert res == ['a']


def test_filter_interventions_no_filters(monkeypatch):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.all.return_value = []
    res = filters_module.filter_interventions(statut=None, urgence=None, type=None, technicien_id=None, db=db, user={'id':1})
    assert res == []
