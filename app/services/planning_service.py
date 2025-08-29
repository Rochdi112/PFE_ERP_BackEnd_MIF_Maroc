# app/services/planning_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from app.models.planning import Planning
from app.models.equipement import Equipement
from app.schemas.planning import PlanningCreate


def create_planning(db: Session, data: PlanningCreate) -> Planning:
    """
    Crée un planning de maintenance pour un équipement donné.

    Raises:
        HTTPException 404: si l’équipement est introuvable
    """
    equipement = db.query(Equipement).filter(Equipement.id == data.equipement_id).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    # Normalise la fréquence reçue (str) vers l'enum
    from app.models.planning import FrequencePlanning
    key = str(data.frequence).strip().lower()
    mapping = {
        "journalier": FrequencePlanning.journalier,
        "hebdomadaire": FrequencePlanning.hebdomadaire,
        "mensuel": FrequencePlanning.mensuel,
        "mensuelle": FrequencePlanning.mensuel,
        "trimestriel": FrequencePlanning.trimestriel,
        "trimestrielle": FrequencePlanning.trimestriel,
        "semestriel": FrequencePlanning.semestriel,
        "semestrielle": FrequencePlanning.semestriel,
        "annuel": FrequencePlanning.annuel,
        "annuelle": FrequencePlanning.annuel,
    }
    freq_enum = mapping.get(key)
    if freq_enum is None:
        raise HTTPException(status_code=400, detail="Fréquence invalide")

    planning = Planning(
        frequence=freq_enum,
        prochaine_date=data.prochaine_date,
        derniere_date=data.derniere_date,
        equipement_id=data.equipement_id,
        date_creation=datetime.utcnow()
    )

    db.add(planning)
    db.commit()
    db.refresh(planning)
    return planning


def get_planning_by_id(db: Session, planning_id: int) -> Planning:
    """
    Récupère un planning par son ID.

    Raises:
        HTTPException 404: si le planning est introuvable
    """
    planning = db.query(Planning).filter(Planning.id == planning_id).first()
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    return planning


def get_all_plannings(db: Session) -> list[Planning]:
    """
    Retourne la liste complète des plannings.
    """
    return db.query(Planning).all()


def update_planning_dates(db: Session, planning_id: int, nouvelle_date: datetime) -> Planning:
    """
    Met à jour les dates (dernière/prochaine) d’un planning.

    Raises:
        HTTPException 404: si le planning est introuvable
    """
    planning = get_planning_by_id(db, planning_id)

    planning.derniere_date = planning.prochaine_date
    planning.prochaine_date = nouvelle_date

    db.commit()
    db.refresh(planning)
    return planning

def update_planning_frequence(db: Session, planning_id: int, frequence: str) -> Planning:
    """
    Met à jour la fréquence d'un planning. Accepte une chaîne brute depuis l'API.
    """
    planning = get_planning_by_id(db, planning_id)
    if frequence:
        # Normalise et map vers l'enum FrequencePlanning si possible
        from app.models.planning import FrequencePlanning
        key = str(frequence).strip().lower()
        mapping = {
            "journalier": FrequencePlanning.journalier,
            "hebdomadaire": FrequencePlanning.hebdomadaire,
            "mensuel": FrequencePlanning.mensuel,
            "mensuelle": FrequencePlanning.mensuel,
            "trimestriel": FrequencePlanning.trimestriel,
            "trimestrielle": FrequencePlanning.trimestriel,
            "semestriel": FrequencePlanning.semestriel,
            "semestrielle": FrequencePlanning.semestriel,
            "annuel": FrequencePlanning.annuel,
            "annuelle": FrequencePlanning.annuel,
        }
        planning.frequence = mapping.get(key, planning.frequence)
    db.commit()
    db.refresh(planning)
    return planning

def delete_planning(db: Session, planning_id: int) -> None:
    planning = get_planning_by_id(db, planning_id)
    db.delete(planning)
    db.commit()
