from app.models.user import User, UserRole
from app.models.intervention import Intervention, InterventionType, StatutIntervention, PrioriteIntervention
from datetime import datetime, timedelta


def test_user_role_properties():
    u = User(username="u1", full_name="Full", email="u1@example.com", hashed_password="x", role=UserRole.admin)
    assert u.is_admin
    assert u.is_staff
    assert u.can_manage_users
    u.role = UserRole.technicien
    assert u.is_technicien
    assert u.can_execute_interventions


def test_intervention_properties_and_delay():
    interv = Intervention(titre="t", description="d", type_intervention=InterventionType.preventive, statut=StatutIntervention.ouverte, priorite=PrioriteIntervention.normale, urgence=False, date_creation=datetime.utcnow(), date_limite=datetime.utcnow() + timedelta(days=1))
    assert interv.est_preventive
    assert interv.est_ouverte
    assert not interv.est_terminee
    # simulate closure
    interv.statut = StatutIntervention.cloturee
    assert interv.est_terminee
