# app/api/v1/filters.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.intervention import Intervention, StatutIntervention, InterventionType
from app.schemas.intervention import InterventionOut
from app.core.rbac import get_current_user  # Authentification requise

router = APIRouter(
    prefix="/filters",
    tags=["filtres"],
    responses={404: {"description": "Aucune intervention trouvée"}}
)

# Dépendance DB
# utilise get_db central

@router.get(
    "/interventions",
    response_model=List[InterventionOut],
    summary="Recherche filtrée d’interventions",
    description="Recherche avancée sur les interventions par statut, urgence, type ou technicien."
)
def filter_interventions(
    statut: Optional[StatutIntervention] = Query(None, description="Statut de l’intervention"),
    urgence: Optional[bool] = Query(None, description="Filtrer par urgence (True/False)"),
    type: Optional[InterventionType] = Query(None, description="Type d’intervention"),
    technicien_id: Optional[int] = Query(None, description="ID du technicien affecté"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    query = db.query(Intervention)

    if statut:
        query = query.filter(Intervention.statut == statut)
    if urgence is not None:
        query = query.filter(Intervention.urgence == urgence)
    if type:
        # Attribut ORM est 'type_intervention' (colonne DB 'type')
        query = query.filter(Intervention.type_intervention == type)
    if technicien_id:
        query = query.filter(Intervention.technicien_id == technicien_id)

    return query.all()
