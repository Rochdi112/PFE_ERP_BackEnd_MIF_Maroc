from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.intervention import InterventionCreate, InterventionOut, StatutIntervention
from app.services.intervention_service import (
    create_intervention,
    get_intervention_by_id,
    get_all_interventions,
    update_statut_intervention
)
from app.core.rbac import get_current_user, technicien_required, responsable_required
from app.services.user_service import ensure_user_for_email

router = APIRouter(
    prefix="/interventions",
    tags=["interventions"],
    responses={404: {"description": "Intervention non trouvée"}}
)

# get_db fourni par app.db.database pour permettre l'override en tests

@router.post(
    "/", 
    response_model=InterventionOut,
    summary="Créer une intervention",
    description="Crée une intervention préventive ou corrective. (admin, responsable uniquement)",
    dependencies=[Depends(responsable_required)]
)
def create_new_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # Ajout utilisateur courant ici
):
    # 👇 Assure un user_id valide: si absent dans le token, crée/récupère via email
    user_id = user.get("user_id")
    if user_id is None:
        email = user.get("email")
        role = user.get("role")
        if email:
            ensured = ensure_user_for_email(db, email=email, role=role)
            user_id = ensured.id
    return create_intervention(db, data, user_id=int(user_id))

@router.get(
    "/", 
    response_model=List[InterventionOut],
    summary="Lister les interventions",
    description="Retourne toutes les interventions du système (authentification requise)"
)
def list_interventions(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_all_interventions(db)

@router.get(
    "/{intervention_id}", 
    response_model=InterventionOut,
    summary="Détail d’une intervention",
    description="Récupère les détails d’une intervention par ID (authentification requise)"
)
def get_intervention(intervention_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_intervention_by_id(db, intervention_id)

@router.patch(
    "/{intervention_id}/statut", 
    response_model=InterventionOut,
    summary="Changer le statut d’une intervention",
    description="Met à jour le statut (cycle de vie) de l’intervention. Action historisée avec l’utilisateur en cours.",
    dependencies=[Depends(technicien_required)]
)
def change_statut_intervention(
    intervention_id: int,
    statut: StatutIntervention,
    remarque: str = "",
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = user.get("user_id")
    if user_id is None:
        email = user.get("email")
        role = user.get("role")
        if email:
            ensured = ensure_user_for_email(db, email=email, role=role)
            user_id = ensured.id
    return update_statut_intervention(
        db=db,
        intervention_id=intervention_id,
        new_statut=statut,
        user_id=int(user_id),
        remarque=remarque
    )
