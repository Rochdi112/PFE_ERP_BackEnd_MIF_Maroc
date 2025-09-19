from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.equipement import Equipement
from app.models.intervention import Intervention
from app.schemas.equipement import EquipementCreate


def create_equipement(db: Session, data: EquipementCreate) -> Equipement:
    if db.query(Equipement).filter(Equipement.nom == data.nom).first():
        raise HTTPException(status_code=400, detail="Équipement déjà existant")
    equipement = Equipement(
        nom=data.nom,
        type_equipement=data.type,
        localisation=data.localisation,
        frequence_entretien_jours=(
            int(data.frequence_entretien)
            if data.frequence_entretien is not None
            else None
        ),
    )
    db.add(equipement)
    db.commit()
    db.refresh(equipement)
    return equipement


def get_equipement_by_id(db: Session, equipement_id: int) -> Equipement:
    equipement = db.query(Equipement).filter(Equipement.id == equipement_id).first()
    if not equipement:
        raise NotFoundException("Équipement")
    return equipement


def get_all_equipements(
    db: Session, *, limit: int = 50, offset: int = 0
) -> list[Equipement]:
    return (
        db.query(Equipement).order_by(Equipement.id).offset(offset).limit(limit).all()
    )


def delete_equipement(db: Session, equipement_id: int) -> None:
    equipement = get_equipement_by_id(db, equipement_id)
    # Protection: empêcher la suppression si des interventions existent
    # (intégrité métier)
    intervention_exists = db.query(
        db.query(Intervention)
        .filter(Intervention.equipement_id == equipement_id)
        .exists()
    ).scalar()

    if intervention_exists:
        raise HTTPException(
            status_code=409, detail="Équipement utilisé par des interventions"
        )
    db.delete(equipement)
    db.commit()
