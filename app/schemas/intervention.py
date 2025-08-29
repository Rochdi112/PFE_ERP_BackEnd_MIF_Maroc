# app/schemas/intervention.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class InterventionType(str, Enum):
    corrective = "corrective"
    preventive = "preventive"
    ameliorative = "ameliorative"
    diagnostic = "diagnostic"

class StatutIntervention(str, Enum):
    ouverte = "ouverte"
    affectee = "affectee"
    en_cours = "en_cours"
    en_attente = "en_attente"
    cloturee = "cloturee"
    annulee = "annulee"
    archivee = "archivee"

class PrioriteIntervention(str, Enum):
    urgente = "urgente"
    haute = "haute"
    normale = "normale"
    basse = "basse"
    programmee = "programmee"

class InterventionBase(BaseModel):
    titre: str
    description: Optional[str] = None
    # Mapping JSON "type" <-> Python "type_intervention"
    type_intervention: InterventionType = Field(..., alias="type")
    statut: Optional[StatutIntervention] = StatutIntervention.ouverte
    priorite: Optional[PrioriteIntervention] = PrioriteIntervention.normale
    urgence: Optional[bool] = False
    date_limite: Optional[datetime] = None

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,  # replaces allow_population_by_field_name
        populate_by_name=True,
    )

class InterventionCreate(InterventionBase):
    technicien_id: Optional[int] = None
    equipement_id: int

class InterventionOut(InterventionBase):
    id: int
    date_creation: datetime
    date_cloture: Optional[datetime] = None
    technicien_id: Optional[int]
    equipement_id: Optional[int] = None
