from pydantic import BaseModel, field_serializer, ConfigDict
from typing import Optional
from datetime import datetime
from app.db.database import Base


# ---------- BASE ----------

class PlanningBase(BaseModel):
    """
    Champs communs pour un planning préventif :
    - fréquence de maintenance
    - dates prévisionnelle et dernière exécution
    """
    frequence: str  # Exemple : "mensuel", "hebdomadaire"
    prochaine_date: Optional[datetime] = None
    derniere_date: Optional[datetime] = None


# ---------- CRÉATION ----------

class PlanningCreate(PlanningBase):
    """
    Schéma utilisé lors de la création d’un planning :
    - nécessite un `equipement_id`
    """
    equipement_id: int


# ---------- RÉPONSE ----------

class PlanningOut(PlanningBase):
    """
    Schéma renvoyé par l’API pour lecture d’un planning :
    - inclut ID, équipement et date de création
    """
    id: int
    equipement_id: int
    date_creation: datetime

    # Pydantic v2 model config (replaces class Config with orm_mode=True)
    model_config = ConfigDict(from_attributes=True)

    # Pydantic v2 field serializer to expose feminine labels expected by tests
    @field_serializer('frequence')
    def serialize_frequence(self, v):
        # v may be enum or string
        val = getattr(v, 'value', v)
        mapping = {
            'mensuel': 'mensuelle',
            'trimestriel': 'trimestrielle',
            'semestriel': 'semestrielle',
            'annuel': 'annuelle',
            'hebdomadaire': 'hebdomadaire',
            'journalier': 'journalier',
        }
        return mapping.get(val, val)
