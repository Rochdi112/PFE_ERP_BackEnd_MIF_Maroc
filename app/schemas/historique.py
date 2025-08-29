from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.intervention import StatutIntervention
from app.schemas.user import UserOut
from app.db.database import Base


# ---------- BASE ----------

class HistoriqueBase(BaseModel):
    """
    Champs communs à tous les historiques :
    - statut à cet instant
    - remarque libre
    """
    statut: StatutIntervention
    remarque: Optional[str] = None


# ---------- CRÉATION ----------

class HistoriqueCreate(HistoriqueBase):
    """
    Payload de création d’un historique :
    - utilisateur et intervention associés requis
    """
    intervention_id: int
    user_id: int


# ---------- RÉPONSE ----------

class HistoriqueOut(HistoriqueBase):
    """
    Schéma de sortie d’un historique (GET) :
    - horodatage + intervention_id + détails de l’utilisateur
    """
    id: int
    horodatage: datetime
    intervention_id: int
    user: UserOut

    model_config = ConfigDict(from_attributes=True)
