from datetime import datetime, timedelta

from app.schemas.equipement import EquipementCreate
from app.schemas.planning import PlanningCreate
from app.services.equipement_service import create_equipement
from app.services.intervention_service import create_intervention_from_planning
from app.services.planning_service import create_planning


def test_create_intervention_from_planning(db_session):
    eq = create_equipement(
        db_session,
        EquipementCreate(
            nom="PINT", type="t", localisation="L", frequence_entretien="7"
        ),
    )
    pc = PlanningCreate(
        frequence="mensuel",
        prochaine_date=datetime.utcnow() + timedelta(days=30),
        derniere_date=None,
        equipement_id=eq.id,
    )
    p = create_planning(db_session, pc)
    inter = create_intervention_from_planning(db_session, p)
    assert inter is not None
