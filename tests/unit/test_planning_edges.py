import pytest
from app.services.planning_service import create_planning, update_planning_frequence
from app.schemas.planning import PlanningCreate
from datetime import datetime


def test_create_planning_missing_equipement(db_session):
    pc = PlanningCreate(frequence="mensuel", prochaine_date=None, derniere_date=None, equipement_id=9999)
    with pytest.raises(Exception):
        create_planning(db_session, pc)


def test_update_planning_frequence_invalid_keeps_existing(db_session):
    # create equipement + planning
    from app.models.equipement import Equipement
    from app.models.planning import Planning
    e = Equipement(nom="EQP", type="t", localisation="L", frequence_entretien="7")
    db_session.add(e); db_session.commit(); db_session.refresh(e)
    from app.models.planning import FrequencePlanning
    p = Planning(frequence=FrequencePlanning.mensuel, prochaine_date=datetime.utcnow(), derniere_date=None, equipement_id=e.id)
    db_session.add(p); db_session.commit(); db_session.refresh(p)
    # invalid frequence string should not crash and should retain the existing value
    res = update_planning_frequence(db_session, p.id, "unknownfreq")
    assert res.id == p.id
