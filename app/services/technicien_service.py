# app/services/technicien_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.technicien import Competence, DisponibiliteTechnicien, Technicien
from app.models.user import User, UserRole
from app.schemas.technicien import CompetenceCreate, TechnicienCreate


def create_technicien(db: Session, data: TechnicienCreate) -> Technicien:
    """
    Crée un technicien en vérifiant que l'utilisateur existe
    et qu'il a bien le rôle "technicien".
    Peut associer des compétences existantes.
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur lié introuvable")
    if user.role != UserRole.technicien:
        raise HTTPException(
            status_code=400, detail="L'utilisateur n’est pas un technicien"
        )

    dispo_value = data.disponibilite
    if isinstance(dispo_value, str):
        # normalise en minuscule et mappe si possible
        lower = dispo_value.strip().lower()
        try:
            dispo_value = DisponibiliteTechnicien(lower)
        except Exception:
            dispo_value = DisponibiliteTechnicien.disponible
    technicien = Technicien(
        user_id=data.user_id, equipe=data.equipe, disponibilite=dispo_value
    )

    if data.competences_ids:
        competences = (
            db.query(Competence).filter(Competence.id.in_(data.competences_ids)).all()
        )
        if len(competences) != len(data.competences_ids):
            raise HTTPException(
                status_code=404, detail="Une ou plusieurs compétences sont introuvables"
            )
        technicien.competences = competences

    db.add(technicien)
    db.commit()
    db.refresh(technicien)
    return technicien


def get_technicien_by_id(db: Session, technicien_id: int) -> Technicien:
    """
    Récupère un technicien par son ID.
    """
    technicien = db.query(Technicien).filter(Technicien.id == technicien_id).first()
    if not technicien:
        raise HTTPException(status_code=404, detail="Technicien introuvable")
    return technicien


def get_all_techniciens(db: Session) -> list[Technicien]:
    """
    Retourne la liste complète des techniciens.
    """
    return db.query(Technicien).all()


def create_competence(db: Session, data: CompetenceCreate) -> Competence:
    """
    Crée une nouvelle compétence, en vérifiant l'unicité.
    """
    existing = db.query(Competence).filter(Competence.nom == data.nom).first()
    if existing:
        raise HTTPException(status_code=400, detail="Compétence déjà existante")

    # Le champ domaine est NOT NULL en base, fournir une valeur par défaut
    competence = Competence(nom=data.nom, domaine="general")
    db.add(competence)
    db.commit()
    db.refresh(competence)
    return competence


def get_all_competences(db: Session) -> list[Competence]:
    """
    Liste toutes les compétences existantes.
    """
    return db.query(Competence).all()
