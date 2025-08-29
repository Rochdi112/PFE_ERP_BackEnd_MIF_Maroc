from sqlalchemy.orm import Session
from app.models.equipement import Equipement
from app.schemas.equipement import EquipementCreate
from app.core.exceptions import NotFoundException
from fastapi import HTTPException

def create_equipement(db: Session, data: EquipementCreate) -> Equipement:
    if db.query(Equipement).filter(Equipement.nom == data.nom).first():
        raise HTTPException(status_code=400, detail="Équipement déjà existant")
    equipement = Equipement(
        nom=data.nom,
        type_equipement=data.type,
        localisation=data.localisation,
        frequence_entretien_jours=int(data.frequence_entretien) if data.frequence_entretien is not None else None,
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

def get_all_equipements(db: Session) -> list[Equipement]:
    return db.query(Equipement).all()

def delete_equipement(db: Session, equipement_id: int) -> None:
    equipement = get_equipement_by_id(db, equipement_id)
    # Protection: empêcher la suppression si des interventions existent (intégrité métier)
    count_interventions = 0
    if hasattr(equipement, "interventions"):
        try:
            # relationship lazy="dynamic" -> count() ne charge pas toute la collection
            count_interventions = equipement.interventions.count()
        except Exception:
            # Si le comptage échoue (p.ex. contexte non initialisé), on considère 0
            count_interventions = 0
    if count_interventions > 0:
        raise HTTPException(status_code=409, detail="Équipement utilisé par des interventions")
    db.delete(equipement)
    db.commit()
