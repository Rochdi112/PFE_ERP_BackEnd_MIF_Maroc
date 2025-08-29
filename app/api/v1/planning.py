# app/api/v1/planning.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.database import get_db
from app.schemas.planning import PlanningCreate, PlanningOut
from app.services.planning_service import (
    create_planning,
    get_planning_by_id,
    get_all_plannings,
    update_planning_dates
)
from app.core.rbac import responsable_required, get_current_user, require_roles

router = APIRouter(
    prefix="/planning",
    tags=["planning"],
    responses={404: {"description": "Planning non trouvé"}}
)

# utilise get_db central

# Autorise admin ou responsable
allowed_planning_roles = require_roles("admin", "responsable")

@router.post(
    "/", 
    response_model=PlanningOut,
    status_code=201,
    summary="Créer un planning préventif",
    description="Crée un planning d’entretien pour un équipement donné. (responsable/admin uniquement)",
    dependencies=[Depends(allowed_planning_roles)]
)
def create_new_planning(data: PlanningCreate, db: Session = Depends(get_db)):
    return create_planning(db, data)

@router.get(
    "/", 
    response_model=List[PlanningOut],
    summary="Lister les plannings",
    description="Liste tous les plannings existants (lecture ouverte aux utilisateurs connectés)."
)
def list_all_plannings(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_all_plannings(db)

@router.get(
    "/{planning_id}", 
    response_model=PlanningOut,
    summary="Détail d’un planning",
    description="Récupère les informations d’un planning par ID."
)
def get_planning(planning_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_planning_by_id(db, planning_id)

@router.patch(
    "/{planning_id}/dates",
    response_model=PlanningOut,
    summary="Mettre à jour la prochaine date d’un planning",
    description="Permet de replanifier la prochaine date de maintenance. (responsable uniquement)",
    dependencies=[Depends(responsable_required)]
)
def update_planning_next_date(
    planning_id: int,
    nouvelle_date: datetime,
    db: Session = Depends(get_db)
):
    return update_planning_dates(db, planning_id, nouvelle_date)

# Ajoute un endpoint PUT simple pour mettre à jour la fréquence (conforme aux tests)
from fastapi import Body
@router.put(
    "/{planning_id}",
    response_model=PlanningOut,
    summary="Mettre à jour un planning",
    dependencies=[Depends(allowed_planning_roles)]
)
def update_planning(planning_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    from app.services.planning_service import update_planning_frequence
    frequence = payload.get("frequence")
    return update_planning_frequence(db, planning_id, frequence)

@router.delete(
    "/{planning_id}",
    status_code=204,
    summary="Supprimer un planning",
    dependencies=[Depends(allowed_planning_roles)]
)
def delete_planning_endpoint(planning_id: int, db: Session = Depends(get_db)):
    from app.services.planning_service import delete_planning
    delete_planning(db, planning_id)
    return
