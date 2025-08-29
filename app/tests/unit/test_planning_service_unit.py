import pytest
from app.services.planning_service import create_planning
from app.schemas.planning import PlanningCreate
from app.services.equipement_service import create_equipement
from app.schemas.equipement import EquipementCreate
from datetime import datetime, timedelta


def test_create_planning_invalid_equipement_raises(db_session):
    pc = PlanningCreate(frequence="mensuel", prochaine_date=datetime.utcnow(), derniere_date=None, equipement_id=999999)
    with pytest.raises(Exception):
        create_planning(db_session, pc)


def test_create_planning_and_update(db_session):
    eq = create_equipement(db_session, EquipementCreate(nom="PL2", type="t", localisation="L", frequence_entretien="7"))
    pc = PlanningCreate(frequence="mensuel", prochaine_date=datetime.utcnow()+timedelta(days=30), derniere_date=None, equipement_id=eq.id)
    p = create_planning(db_session, pc)
    assert p.id is not None
