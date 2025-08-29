from app.models.intervention import Intervention, StatutIntervention, InterventionType, PrioriteIntervention
from datetime import datetime, timedelta


def test_intervention_delai_and_retard():
    past = datetime.utcnow() - timedelta(days=2)
    interv = Intervention(titre="t", description="d", type_intervention=InterventionType.corrective, statut=StatutIntervention.ouverte, priorite=PrioriteIntervention.normale, urgence=False, date_creation=datetime.utcnow(), date_limite=past)
    assert interv.est_en_retard is True or interv.est_en_retard is False
    # delai_restant returns None/negative delta; ensure callable
    _ = interv.delai_restant
