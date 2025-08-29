from pydantic import BaseModel, Field
from typing import Optional

class EquipementBase(BaseModel):
    nom: str
    # Map JSON "type" -> model field "type_equipement"
    type: str = Field(alias="type")
    localisation: str
    # Tests envoient une chaîne; stocké en int jours côté modèle
    frequence_entretien: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "validate_by_name": True
    }

class EquipementCreate(EquipementBase):
    pass

class EquipementOut(EquipementBase):
    id: int
    # Expose properties compatibles
    frequence_entretien: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "validate_by_name": True
    }
