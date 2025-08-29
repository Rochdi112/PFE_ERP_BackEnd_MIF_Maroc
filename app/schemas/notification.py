from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.db.database import Base


# ---------- BASE ----------

class NotificationBase(BaseModel):
    """
    Champs de base pour une notification :
    - type : ex: affectation, clôture
    - canal : ex: email, log
    - contenu : texte affiché dans l'email ou log
    """
    type_notification: str = Field(..., alias="type")
    canal: str
    contenu: Optional[str] = None


# ---------- CRÉATION ----------

class NotificationCreate(NotificationBase):
    """
    Schéma pour création d’une notification liée à une intervention et un utilisateur
    """
    intervention_id: int
    user_id: int


# ---------- RÉPONSE API ----------

class NotificationOut(NotificationBase):
    """
    Schéma renvoyé par l’API avec métadonnées :
    - date d’envoi, ids liés
    """
    id: int
    date_envoi: datetime
    intervention_id: int
    user_id: int

    # Pydantic v2 config for from_attributes + validate by field name
    model_config = {
        "from_attributes": True,
        "validate_by_name": True,
    }
