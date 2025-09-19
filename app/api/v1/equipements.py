from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.rbac import responsable_required
from app.db.database import get_db
from app.schemas.equipement import EquipementCreate, EquipementOut
from app.services.equipement_service import (
    create_equipement,
    delete_equipement,
    get_all_equipements,
    get_equipement_by_id,
)

router = APIRouter(
    prefix="/equipements",
    tags=["equipements"],
    responses={404: {"description": "Équipement non trouvé"}},
)


@router.post(
    "/",
    response_model=EquipementOut,
    summary="Créer un équipement",
    dependencies=[Depends(responsable_required)],
)
def create_new_equipement(
    data: EquipementCreate,
    db: Session = Depends(get_db),
):
    """
    Crée un nouvel équipement (Accès : responsable).
    """
    return create_equipement(db, data)


@router.get(
    "/",
    response_model=List[EquipementOut],
    summary="Lister les équipements",
)
def list_equipements(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Liste tous les équipements.
    """
    return get_all_equipements(db, limit=limit, offset=offset)


@router.get(
    "/{equipement_id}",
    response_model=EquipementOut,
    summary="Détail d'un équipement",
)
def get_equipement(equipement_id: int, db: Session = Depends(get_db)):
    """
    Récupère le détail d'un équipement par son ID.
    """
    return get_equipement_by_id(db, equipement_id)


@router.delete(
    "/{equipement_id}",
    summary="Supprimer un équipement",
    dependencies=[Depends(responsable_required)],
)
def delete_equipement_by_id(equipement_id: int, db: Session = Depends(get_db)):
    """
    Supprime un équipement par ID (Accès : responsable).
    """
    delete_equipement(db, equipement_id)
    return {"detail": "Équipement supprimé avec succès."}
