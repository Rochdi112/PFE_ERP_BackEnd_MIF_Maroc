# app/api/v1/techniciens.py

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import (
    get_current_user,
    responsable_required,
)
from app.db.database import get_db
from app.models.technicien import DisponibiliteTechnicien
from app.models.technicien import Technicien as TechnicienModel
from app.schemas.technicien import (
    CompetenceCreate,
    CompetenceOut,
    TechnicienBase,
    TechnicienCreate,
    TechnicienOut,
)
from app.services.technicien_service import (
    create_competence,
    create_technicien,
    get_all_competences,
    get_all_techniciens,
    get_technicien_by_id,
)

router = APIRouter(
    prefix="/techniciens",
    tags=["techniciens"],
    responses={404: {"description": "Technicien ou compétence introuvable"}},
)


@router.post("/", response_model=TechnicienOut, summary="Créer un technicien")
def create_new_technicien(
    data: TechnicienCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(responsable_required),
):
    """
    Crée un nouveau technicien (réservé aux responsables).
    """
    return create_technicien(db, data)


@router.get(
    "/",
    response_model=List[TechnicienOut],
    summary="Lister les techniciens",
)
def list_techniciens(
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)
):
    """
    Liste tous les techniciens.
    """
    return get_all_techniciens(db)


@router.post(
    "/competences",
    response_model=CompetenceOut,
    summary="Créer une compétence",
)
def create_new_competence(
    data: CompetenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(responsable_required),
):
    """
    Crée une nouvelle compétence (réservé aux responsables).
    """
    return create_competence(db, data)


@router.get(
    "/competences",
    response_model=List[CompetenceOut],
    summary="Lister les compétences",
)
def list_competences(
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)
):
    """
    Liste toutes les compétences.
    """
    return get_all_competences(db)


@router.get(
    "/{technicien_id}",
    response_model=TechnicienOut,
    summary="Détail d'un technicien",
)
def get_technicien(
    technicien_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Récupère le détail d’un technicien par ID.
    """
    return get_technicien_by_id(db, technicien_id)


@router.put(
    "/{technicien_id}",
    response_model=TechnicienOut,
    summary="Mettre à jour un technicien",
)
def update_technicien(
    technicien_id: int,
    data: TechnicienBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(responsable_required),
):
    t = db.query(TechnicienModel).filter(TechnicienModel.id == technicien_id).first()
    if not t:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Technicien introuvable")
    # Normalisation simple de la disponibilité si string
    dispo = data.disponibilite
    if isinstance(dispo, str) and dispo:
        try:
            t.disponibilite = DisponibiliteTechnicien(dispo.strip().lower())
        except Exception:
            pass
    t.equipe = data.equipe if data.equipe is not None else t.equipe
    db.commit()
    db.refresh(t)
    return t


@router.delete(
    "/{technicien_id}",
    summary="Supprimer un technicien",
    status_code=204,
)
def delete_technicien(
    technicien_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(responsable_required),
):
    t = db.query(TechnicienModel).filter(TechnicienModel.id == technicien_id).first()
    if not t:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Technicien introuvable")
    db.delete(t)
    db.commit()
    return
