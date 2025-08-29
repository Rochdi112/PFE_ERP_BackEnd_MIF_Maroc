import pytest
from app.services.equipement_service import create_equipement
from app.schemas.equipement import EquipementCreate


def test_create_duplicate_equipement_raises(db_session):
    data = EquipementCreate(nom="DUP2", type="t", localisation="L", frequence_entretien="7")
    create_equipement(db_session, data)
    with pytest.raises(Exception):
        create_equipement(db_session, data)
